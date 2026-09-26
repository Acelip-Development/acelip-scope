"""Pure parsers; importing this module never runs a diagnostic."""

import csv
import io
import re


def memory_info(text: str) -> dict[str, int]:
    return {key: int(value.split()[0]) * 1024
            for line in text.splitlines() if ':' in line
            for key, value in [line.split(':', 1)] if value.strip()}


def format_bytes(value: int | float) -> str:
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'):
        if abs(value) < 1024 or unit == 'PiB':
            return f"{value:.1f} {unit}"
        value /= 1024
    return str(value)


GPU_FIELDS = ('name', 'driver', 'temperature', 'utilization', 'memory_used',
              'memory_total', 'power', 'fan')


def nvidia_csv(text: str) -> list[dict[str, str]]:
    rows = []
    for row in csv.reader(io.StringIO(text), skipinitialspace=True):
        if not row:
            continue
        if len(row) != len(GPU_FIELDS):
            raise ValueError(f"Expected {len(GPU_FIELDS)} NVIDIA fields, received {len(row)}")
        rows.append(dict(zip(GPU_FIELDS, (v.strip() for v in row))))
    return rows


def cuda_version(text: str) -> str | None:
    match = re.search(r'CUDA Version:\s*([\d.]+)', text)
    return match.group(1) if match else None


def temperatures(data: dict, cpu_only: bool = False) -> list[tuple[str, float]]:
    found = []
    for chip, fields in data.items():
        if cpu_only and not chip.lower().startswith(('coretemp', 'k10temp', 'zenpower', 'cpu_thermal')):
            continue
        if not isinstance(fields, dict):
            continue
        for label, values in fields.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    if re.fullmatch(r'temp\d+_input', key) and isinstance(value, (float, int)) and -20 <= value <= 150:
                        found.append((f"{chip} / {label}", float(value)))
    return found


def flatten_tree(items: list[dict]):
    for item in items:
        yield item
        yield from flatten_tree(item.get('children') or [])


def usage_status(percent: float) -> str:
    return 'error' if percent >= 95 else 'warning' if percent >= 85 else 'ok'


def vpn_interfaces(interfaces: list[dict]) -> list[str]:
    found = []
    for item in interfaces:
        name = item.get('ifname', '')
        kind = (item.get('linkinfo') or {}).get('info_kind', '')
        if kind in {'wireguard', 'tun', 'tap', 'ppp'} or name.lower().startswith(
                ('tun', 'tap', 'wg', 'tailscale', 'zt', 'ppp', 'proton', 'mullvad')):
            found.append(name)
    return found


def smart_summary(data: dict) -> tuple[str, str, str]:
    """Decode SMART health independently of smartctl's bitmask exit code."""
    passed = (data.get('smart_status') or {}).get('passed')
    nvme = data.get('nvme_smart_health_information_log') or {}
    critical = int(str(nvme.get('critical_warning', 0)), 0)
    temp = (data.get('temperature') or {}).get('current', nvme.get('temperature'))
    details = []
    if temp is not None:
        details.append(f"Disk temperature: {temp} °C")
    for key in ('available_spare', 'percentage_used', 'media_errors', 'num_err_log_entries'):
        if key in nvme:
            details.append(f"{key.replace('_', ' ')}: {nvme[key]}")
    if passed is False or critical:
        return 'error', 'Device reports a health failure', '\n'.join(details)
    if nvme.get('media_errors', 0) or nvme.get('percentage_used', 0) >= 100:
        return 'warning', 'Device health counters need review', '\n'.join(details)
    if passed is True or nvme:
        return 'ok', 'Device reports healthy', '\n'.join(details)
    return 'unavailable', 'Device did not expose a SMART health assessment', '\n'.join(details)
