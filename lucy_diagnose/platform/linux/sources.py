"""Describe the read-only evidence source without depending on GTK."""


def source_for(section, title):
    if title.startswith('Disk ·') or title == 'Filesystem usage':
        return 'findmnt · filesystem usage'
    if title.startswith('SMART ·'):
        return 'smartctl --all --json'
    if title.startswith('/dev/'):
        return 'lsblk --json'
    if 'sensor' in title.lower() or title == 'CPU temperature':
        return 'sensors -j'
    if 'GPU' in title or 'NVIDIA' in title or 'VRAM' in title or 'CUDA' in title:
        return 'nvidia-smi · read-only telemetry'
    if title.startswith('Interface ·') or title == 'VPN interfaces':
        return 'ip -j -details address show'
    if title.startswith('Default route'):
        return 'ip -j route show default'
    return {
        'Operating system': '/etc/os-release', 'Kernel': 'uname', 'CPU model': '/proc/cpuinfo',
        'Uptime': '/proc/uptime', 'CPU load': '/proc/loadavg', 'RAM usage': '/proc/meminfo',
        'Swap usage': '/proc/meminfo', 'Failed services / units': 'systemctl --failed',
        'Package database': 'dpkg --audit', 'Held packages': 'apt-mark showhold',
        'Recent journal errors': 'journalctl · visible errors', 'Journal coverage': 'journalctl · access scope',
        'Recent OOM events': 'journalctl · visible kernel journal', 'Ollama service': 'systemctl show ollama.service',
        'Ollama API': 'GET 127.0.0.1:11434/api/version', 'Ollama models': 'GET 127.0.0.1:11434/api/tags',
        'Ollama loaded models': 'GET 127.0.0.1:11434/api/ps', 'DNS': 'resolvectl status',
        'DNS fallback': '/etc/resolv.conf', 'Listening TCP / UDP ports': 'ss -lntu',
        'Internet reachability': 'ping 1.1.1.1', 'Gateway reachability': 'ping · default gateway',
        'Codex': 'codex --version', 'Claude': 'claude --version', 'Gemini': 'gemini --version',
        'Opencode': 'opencode --version', 'LM Studio executable / CLI': 'PATH / common installation paths',
        'LM Studio process': 'ps · process names only',
    }.get(title, f'{section} collector')
