import json
import re
from dataclasses import replace

from .common import json_result, unavailable
from ...models import Check, Status
from ...parsers import flatten_tree, format_bytes, smart_summary, temperatures, usage_status


def filesystem_usage(runner):
    data, error = json_result('Filesystem usage', runner.run('findmnt', '--json', '--bytes', '--real',
                             '--output', 'TARGET,SOURCE,FSTYPE,SIZE,USED,AVAIL,USE%', '-t', 'nosquashfs'))
    if error:
        return [error]
    checks = []
    for fs in flatten_tree(data.get('filesystems', [])):
        raw = fs.get('use%')
        try:
            percent = float(str(raw).rstrip('%'))
            summary = f"{percent:g}% · {format_bytes(int(fs['used']))} / {format_bytes(int(fs['size']))}"
            checks.append(Check(f"Disk · {fs['target']}", summary, Status(usage_status(percent)),
                                f"{fs.get('source')} · {fs.get('fstype')}\nAvailable: {format_bytes(int(fs['avail']))}"))
        except (ValueError, TypeError, KeyError):
            checks.append(Check(f"Disk · {fs.get('target', 'unknown')}", 'Usage not reported', Status.UNAVAILABLE))
    return checks or [Check('Filesystem usage', 'No filesystems reported', Status.UNAVAILABLE)]


def device_health(runner, device):
    path = device.get('path', '')
    if not re.fullmatch(r'/dev/[A-Za-z0-9_.-]+', path):
        return Check('Device health', 'Unsupported device path', Status.UNAVAILABLE)
    result = runner.run('smartctl', '--all', '--json', path, timeout=10)
    # Bits 0..2 indicate command/open/data errors. Higher bits carry health/history.
    if result.problem or result.code is None or result.code < 0 or result.code & 7:
        try:
            messages = json.loads(result.stdout).get('smartctl', {}).get('messages', [])
            reason = '\n'.join(m.get('string', '') for m in messages)
            if reason and not result.problem:
                result = replace(result, stderr=reason)
        except (ValueError, TypeError, AttributeError):
            pass
        return unavailable(f'SMART · {path}', result)
    try:
        data = json.loads(result.stdout)
        status, summary, details = smart_summary(data)
        if result.code & 8:
            status, summary = 'error', 'SMART reports a failing device'
        elif result.code & 0xF0 and status == 'ok':
            status, summary = 'warning', 'SMART attributes or history need review'
        messages = '\n'.join(item.get('string', '') for item in data.get('smartctl', {}).get('messages', []))
        evidence = json.dumps(data, indent=2, ensure_ascii=False)
        return Check(f'SMART · {path}', summary, Status(status),
                     '\n'.join(part for part in (details, messages, evidence) if part))
    except (ValueError, TypeError, AttributeError) as exc:
        return Check(f'SMART · {path}', 'Unrecognized device response', Status.UNAVAILABLE, str(exc))


def collect(runner):
    checks = filesystem_usage(runner)
    data, error = json_result('Block devices', runner.run('lsblk', '--json', '--output',
                             'NAME,PATH,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL,TRAN', '--exclude', '7'))
    if error:
        checks.append(error)
    else:
        devices = list(flatten_tree(data.get('blockdevices', [])))
        for device in devices:
            mounts = ', '.join(m for m in (device.get('mountpoints') or []) if m) or 'Not mounted'
            checks.append(Check(device.get('path', device.get('name', 'Device')),
                                f"{device.get('size', '?')} · {device.get('fstype') or device.get('type', '?')}",
                                details=f"{device.get('model') or ''}\n{mounts}\nTransport: {device.get('tran') or 'unknown'}"))
            if device.get('type') == 'disk':
                checks.append(device_health(runner, device))
        if not devices:
            checks.append(Check('Block devices', 'No devices exposed', Status.UNAVAILABLE))
    data, error = json_result('Disk sensors', runner.run('sensors', '-j'))
    if error:
        checks.append(error)
    else:
        values = [(name, value) for name, value in temperatures(data)
                  if name.lower().startswith(('nvme', 'drivetemp'))]
        checks.append(Check('Disk temperature sensors', f'{len(values)} readings available' if values else 'No disk sensors exposed',
                            Status.INFO if values else Status.UNAVAILABLE,
                            '\n'.join(f'{name}: {value:.1f} °C' for name, value in values)))
    checks.append(Check('Storage access', 'SMART/NVMe checks use current user permissions', details=
                        'smartctl reads ATA and NVMe health. No self-tests, device configuration, or elevation are performed. '
                        'Sensor chip identifiers are shown without assuming a device mapping.'))
    return checks
