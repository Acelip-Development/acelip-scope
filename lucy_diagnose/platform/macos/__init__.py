"""Architecture placeholder only; no macOS diagnostics are implemented."""
from ..base import UnsupportedPlatform


class MacOSPlatform(UnsupportedPlatform):
    name = 'macOS'
