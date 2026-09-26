"""Lightweight samples only; no journal, SMART, network probes, or AI clients."""

import csv
from datetime import datetime
import io
import math
from pathlib import Path

from ...parsers import format_bytes, memory_info

from ...telemetry import METRICS, Sample
from .sensors import read_hwmon, primary_cpu


def cpu_counters(text):
    first = text.splitlines()[0].split()
    if first[0] != 'cpu' or len(first) < 5:
        raise ValueError('Missing aggregate CPU counters')
    values = [int(v) for v in first[1:9]]  # guest time is already included in user/nice.
    return sum(values), values[3] + (values[4] if len(values) > 4 else 0)


def cpu_percent(previous, current):
    if previous is None or current[0] <= previous[0] or current[1] < previous[1]:
        return None
    return max(0., min(100., 100 * (1 - (current[1] - previous[1]) / (current[0] - previous[0]))))


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


class TelemetrySampler:
    def __init__(self, reader=None, hwmon=Path('/sys/class/hwmon')):
        self.reader = reader or (lambda path: Path(path).read_text())
        self.hwmon = hwmon
        self.previous_cpu = None
        self.epoch = None

    def sample(self, runner, epoch=None):
        if epoch is not None and epoch != self.epoch:
            self.previous_cpu, self.epoch = None, epoch
        sample = Sample(datetime.now().astimezone())
        try:
            current = cpu_counters(self.reader('/proc/stat'))
            sample.values['cpu'] = cpu_percent(self.previous_cpu, current)
            sample.notes['cpu'] = 'Across all logical CPUs' if sample.values['cpu'] is not None else 'Waiting for a second sample'
            self.previous_cpu = current
        except (OSError, ValueError, IndexError):
            self.previous_cpu = None
            sample.notes['cpu'] = 'CPU counters unavailable'
        try:
            memory = memory_info(self.reader('/proc/meminfo'))
            total = memory['MemTotal']
            used = total - memory.get('MemAvailable', memory.get('MemFree', 0))
            sample.values['ram'] = max(0, min(100, used * 100 / total))
            sample.notes['ram'] = f'{format_bytes(used)} / {format_bytes(total)}'
        except (OSError, ValueError, KeyError, ZeroDivisionError):
            sample.notes['ram'] = 'Memory counters unavailable'
        primary = primary_cpu(read_hwmon(self.hwmon))
        sample.values['cpu_temp'] = primary.value if primary else None
        sample.notes['cpu_temp'] = f'Primary CPU sensor · {primary.chip} / {primary.label}' if primary else 'No accessible CPU sensor'
        result = runner.run('nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total',
                            '--format=csv,noheader,nounits', timeout=1.5)
        if result.ok:
            try:
                rows = list(csv.reader(io.StringIO(result.stdout), skipinitialspace=True))
                used_pct, temp, used, total = [number(v) for v in rows[0]]
                valid_memory = used is not None and total is not None and 0 <= used <= total and total > 0
                sample.values.update(gpu=used_pct if used_pct is not None and 0 <= used_pct <= 100 else None,
                                     gpu_temp=temp if temp is not None and -20 <= temp <= 150 else None,
                                     vram=used * 100 / total if valid_memory else None)
                sample.notes['gpu'] = 'NVIDIA GPU 1' + (f' of {len(rows)}' if len(rows) > 1 else '')
                sample.notes['gpu_temp'] = 'NVIDIA GPU 1 sensor'
                sample.notes['vram'] = f'{used:g} / {total:g} MiB' if valid_memory else 'VRAM unavailable'
            except (ValueError, IndexError, TypeError):
                sample.notes['gpu'] = 'Unrecognized GPU response'
        else:
            for key in ('gpu', 'gpu_temp', 'vram'):
                sample.notes[key] = result.problem or 'GPU telemetry unavailable'
        return sample
