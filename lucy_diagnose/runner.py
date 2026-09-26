"""Compatibility facade; execution belongs to the selected platform backend."""
from .commands import Result


def Runner(cancel=None, max_bytes=262144):
    from .platform.detect import get_platform
    return get_platform().create_runner(cancel, max_bytes=max_bytes)
