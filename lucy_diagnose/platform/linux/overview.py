import os
import platform

from .common import json_result, read_text, unavailable
from ...models import Check, Status
from ...parsers import cuda_version, format_bytes, memory_info, nvidia_csv, temperatures
from .distro import detect_distro
from .desktop import detect_desktop
from .sensors import sensor_checks


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
    distro = detect_distro()
    checks.append(Check('Operating system', distro.name, details=f'ID: {distro.id}\nFamily: {distro.family}\nVersion: {distro.version_id}\nID_LIKE: {", ".join(distro.id_like)}', source='/etc/os-release'))
    desktop = detect_desktop()
    checks.append(Check('Desktop environment', f'{desktop.environment} · {desktop.display_server}',
                        details=f'Session: {desktop.session_name}', source='Desktop session environment', support=desktop.support))
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
    checks.extend(sensor_checks(runner))
    checks.extend(collect_gpu(runner))
    from .storage import filesystem_usage
    checks.extend(filesystem_usage(runner))
    return checks
