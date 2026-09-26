"""Read freedesktop release metadata as data, never as shell code."""
from pathlib import Path
import re
import shlex
from ...models import DistroInfo

FAMILIES = {'debian': {'debian', 'ubuntu', 'linuxmint', 'pop', 'pop_os'},
            'fedora-rhel': {'fedora', 'rhel', 'rocky', 'almalinux', 'centos', 'centos-stream', 'ol'},
            'arch': {'arch', 'archlinux', 'endeavouros', 'manjaro', 'garuda'},
            'opensuse': {'opensuse', 'opensuse-leap', 'opensuse-tumbleweed', 'suse', 'sles'}}


def parse_os_release(text):
    values = {}
    for line in text.splitlines():
        key, sep, value = line.partition('=')
        if not sep or not re.fullmatch('[A-Z_]+', key):
            continue
        try:
            parts = shlex.split(value, comments=True)
            if len(parts) == 1:
                values[key] = parts[0]
        except ValueError:
            continue
    identifier = values.get('ID', 'unknown').lower()
    likes = tuple(values.get('ID_LIKE', '').lower().split())
    family = next((family for candidate in (identifier, *likes)
                   for family, members in FAMILIES.items() if candidate in members), 'unknown')
    return DistroInfo(identifier, values.get('PRETTY_NAME', values.get('NAME', 'Unknown Linux distribution')),
                     values.get('VERSION', ''), values.get('VERSION_ID', ''), likes, family)


def detect_distro(paths=(Path('/etc/os-release'), Path('/usr/lib/os-release'))):
    for path in paths:
        try:
            text = path.read_text(errors='replace')
            info = parse_os_release(text)
            if info.id != 'unknown' or info.name != 'Unknown Linux distribution':
                return info
        except OSError:
            continue
    return DistroInfo()
