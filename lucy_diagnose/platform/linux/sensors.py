"""Semantic sensor classification shared by detailed scans and lightweight hwmon reads."""
import json
import math
from pathlib import Path
import re
from ...models import Check, SensorReading, Status, Support

CPU_CHIPS = ('k10temp', 'coretemp', 'zenpower', 'cpu_thermal')


def sensor_kind(chip, label, unit):
    chip, label = chip.lower(), label.lower()
    if unit == 'RPM':
        return 'pump' if 'pump' in label else 'fan'
    if chip.startswith(CPU_CHIPS):
        return 'cpu'
    if any(term in label for term in ('coolant', 'liquid', 'water')) or any(term in chip for term in ('kraken', 'corsair', 'aquacomputer', 'liquidctl')):
        return 'coolant'
    if chip.startswith(('nvme', 'drivetemp')):
        return 'storage'
    if chip.startswith(('amdgpu', 'nouveau', 'nvidia')):
        return 'gpu'
    if chip.startswith(('jc42', 'spd', 'ee1004')) or 'dimm' in label:
        return 'memory'
    if chip.startswith(('mlx', 'iwlwifi', 'ath', 'r8169', 'igc', 'i40e', 'ice', 'bnxt', 'enp', 'eth')):
        return 'network'
    return 'other'


def make_reading(chip, label, value, unit, source):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(value) or not ((0 <= value <= 100000) if unit == 'RPM' else (-30 <= value <= 150)):
        return None
    return SensorReading(chip, label, value, unit, sensor_kind(chip, label, unit), source)


def parse_sensors(data):
    readings = []
    if not isinstance(data, dict):
        return readings
    for chip, fields in data.items():
        if not isinstance(fields, dict):
            continue
        for label, values in fields.items():
            if not isinstance(values, dict):
                continue
            for key, value in values.items():
                match = re.fullmatch(r'(temp|fan)\d+_input', key)
                if match:
                    reading = make_reading(chip, label, value, 'RPM' if match[1] == 'fan' else '°C', 'sensors -j')
                    if reading:
                        readings.append(reading)
    return readings


def read_hwmon(root=Path('/sys/class/hwmon')):
    readings = []
    try:
        chips = sorted(root.glob('hwmon*'))
    except OSError:
        return readings
    for chip in chips:
        try:
            name = (chip / 'name').read_text().strip()
            paths = sorted(chip.glob('*_input'))
        except OSError:
            continue
        for path in paths:
            match = re.fullmatch(r'(temp|fan)\d+_input', path.name)
            if not match:
                continue
            try:
                unit = 'RPM' if match[1] == 'fan' else '°C'
                value = float(path.read_text()) / (1 if unit == 'RPM' else 1000)
                try:
                    label = path.with_name(path.name.replace('_input', '_label')).read_text().strip()
                except OSError:
                    label = path.name.replace('_input', '')
                reading = make_reading(name, label, value, unit, str(path))
                if reading:
                    readings.append(reading)
            except (OSError, ValueError):
                continue
    return readings


def primary_cpu(readings):
    candidates = [r for r in readings if r.kind == 'cpu' and r.unit == '°C']
    def priority(reading):
        chip, label = reading.chip.lower(), reading.label.lower()
        if chip.startswith('k10temp') and label == 'tctl':
            rank = 0
        elif label == 'tdie':
            rank = 1
        elif chip.startswith('coretemp') and ('package' in label or label == 'physical id 0'):
            rank = 2
        elif label == 'tctl':
            rank = 3
        else:
            rank = 4
        # Within the same semantic class, show the warmest CPU package/core.
        return rank, -reading.value, reading.chip, reading.label
    return min(candidates, key=priority) if candidates else None


def sensor_status(runner, hwmon=Path('/sys/class/hwmon')):
    result = runner.run('sensors', '-j')
    readings = []
    if result.ok:
        try:
            readings = parse_sensors(json.loads(result.stdout))
        except ValueError:
            pass
    if readings:
        return readings, Support.SUPPORTED
    readings = read_hwmon(hwmon)
    return readings, Support.PARTIAL if readings else Support.UNAVAILABLE


def sensor_checks(runner):
    readings, support = sensor_status(runner)
    primary = primary_cpu(readings)
    lines = lambda items: '\n'.join(f'{r.kind} · {r.chip} / {r.label}: {r.value:g} {r.unit}' for r in items)
    checks = [Check('CPU temperature', f'{primary.value:.1f} °C' if primary else 'No recognized CPU sensor',
                    Status.INFO if primary else Status.UNAVAILABLE,
                    ('Primary CPU sensor: ' + primary.chip + ' / ' + primary.label + '\n' if primary else '') + lines(r for r in readings if r.kind == 'cpu'),
                    source=primary.source if primary else 'Linux sensor inspection', support=support if primary else Support.UNAVAILABLE)]
    cooling = [r for r in readings if r.kind in {'coolant', 'pump', 'fan'}]
    checks.append(Check('Cooling telemetry', f'{len(cooling)} cooling readings' if cooling else 'No cooling sensors exposed',
                        Status.INFO if cooling else Status.UNAVAILABLE, lines(cooling), source='Linux sensors / hwmon',
                        support=support if cooling else Support.UNAVAILABLE))
    others = [r for r in readings if r.kind not in {'cpu', 'coolant', 'pump', 'fan'}]
    checks.append(Check('Other hardware sensors', f'{len(others)} readings', Status.INFO, lines(others), source='Linux sensors / hwmon', support=support))
    return checks
