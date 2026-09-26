"""Lazy platform selection. Unsupported hosts never import Linux probes."""
import platform
from .base import UnsupportedPlatform


def get_platform(system=None):
    name = (system if system is not None else platform.system()).casefold()
    if name == 'linux':
        from .linux.backend import LinuxPlatform
        return LinuxPlatform()
    if name == 'windows':
        from .windows import WindowsPlatform
        return WindowsPlatform()
    if name in {'darwin', 'macos'}:
        from .macos import MacOSPlatform
        return MacOSPlatform()
    return UnsupportedPlatform()
