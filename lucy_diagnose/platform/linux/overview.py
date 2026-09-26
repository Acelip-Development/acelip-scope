import os
import platform

from .common import json_result, read_text, unavailable
from ...models import Check, Status
from ...parsers import cuda_version, format_bytes, memory_info, nvidia_csv, temperatures


def collect_gpu(runner):
    result = runner.run('nvidia-smi', '--query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,fan.speed',
                        '--format=csv,noheader,nounits')
    if not result.ok:
        return [unavailable('NVIDIA GPU', result)]
    try:
        devices = nvidia_csv(result.stdout)
    except ValueError as exc:
        return [Check('NVIDIA GPU', 'Unrecognized output', Status.UNAVAILABLE, str(exc))]
    if not devices:
        return [Check('NVIDIA GPU', 'No NVIDIA devices reported', Status.UNAVAILABLE)]
    checks = []
    for index, gpu in enumerate(devices):
        prefix = f"GPU {index + 1} · " if len(devices) > 1 else ''
        checks.extend([Check(prefix + 'GPU', gpu['name'], Status.OK),
                       Check(prefix + 'NVIDIA driver', gpu['driver'])])
        for title, key, unit in [('GPU temperature', 'temperature', '°C'), ('GPU utilization', 'utilization', '%'),
                                 ('GPU power draw', 'power', 'W'), ('GPU fan speed', 'fan', '%')]:
            value = gpu[key]
            try:
                numeric = float(value)
            except ValueError:
                numeric = None
            if numeric is None:
                checks.append(Check(prefix + title, 'Not exposed by this GPU', Status.UNAVAILABLE))
            else:
                status = Status.WARNING if key == 'temperature' and numeric >= 85 else Status.INFO
                checks.append(Check(prefix + title, f"{value} {unit}", status))
        checks.append(Check(prefix + 'VRAM', f"{gpu['memory_used']} / {gpu['memory_total']} MiB"))
    banner = runner.run('nvidia-smi')
    cuda = cuda_version(banner.stdout) if banner.ok else None
    checks.append(Check('CUDA compatibility', cuda or 'Unavailable', Status.INFO if cuda else Status.UNAVAILABLE,
                        'Maximum CUDA version supported by the driver; this does not verify an installed CUDA toolkit.'))
    return checks


def collect(runner):
    checks = []
    try:
        release = platform.freedesktop_os_release()
        checks.append(Check('Ubuntu version', release.get('PRETTY_NAME', 'Unknown')))
    except OSError as exc:
        checks.append(Check('Ubuntu version', 'Unavailable', Status.UNAVAILABLE, str(exc)))
    checks.append(Check('Kernel', platform.release()))
    try:
        seconds = int(float(read_text('/proc/uptime').split()[0]))
        checks.append(Check('Uptime', f"{seconds // 86400}d {seconds % 86400 // 3600}h {seconds % 3600 // 60}m"))
        cpu = next((line.split(':', 1)[1].strip() for line in read_text('/proc/cpuinfo').splitlines()
                    if line.startswith('model name')), platform.machine())
        checks.append(Check('CPU model', cpu))
        loads = os.getloadavg()
        checks.append(Check('CPU load', ' / '.join(f'{v:.2f}' for v in loads), Status.INFO,
                            f"1 / 5 / 15 minute load averages; {os.cpu_count()} logical CPUs. Load is not utilization percent."))
    except (OSError, ValueError, IndexError) as exc:
        checks.append(Check('CPU / uptime', 'Unavailable', Status.UNAVAILABLE, str(exc)))
    try:
        memory = memory_info(read_text('/proc/meminfo'))
        total = memory['MemTotal']
        available = memory.get('MemAvailable', memory.get('MemFree', 0))
        used = total - available
        checks.append(Check('RAM usage', f"{format_bytes(used)} / {format_bytes(total)}", Status.WARNING if used / total >= .9 else Status.OK,
                            f"{used / total:.1%} used; available memory includes reclaimable caches."))
        swap = memory['SwapTotal']
        checks.append(Check('Swap usage', f"{format_bytes(swap - memory['SwapFree'])} / {format_bytes(swap)}" if swap else 'No swap configured'))
    except (OSError, ValueError, KeyError, ZeroDivisionError) as exc:
        checks.append(Check('Memory', 'Unavailable', Status.UNAVAILABLE, str(exc)))
    data, error = json_result('CPU temperature', runner.run('sensors', '-j'))
    if error:
        checks.append(error)
    else:
        values = temperatures(data, cpu_only=True)
        checks.append(Check('CPU temperature', f"{max(v for _, v in values):.1f} °C" if values else 'No recognized CPU sensor',
                            Status.INFO if values else Status.UNAVAILABLE,
                            '\n'.join(f'{label}: {value:.1f} °C' for label, value in values)))
    checks.extend(collect_gpu(runner))
    from .storage import filesystem_usage
    checks.extend(filesystem_usage(runner))
    return checks
