"""Architecture placeholder only; no Windows diagnostics are implemented."""
from ..base import UnsupportedPlatform


class WindowsPlatform(UnsupportedPlatform):
    name = 'Windows'
