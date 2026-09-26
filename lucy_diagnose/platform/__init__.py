"""Platform factory. Importing this package does not probe or select a backend."""
from .detect import get_platform

__all__ = ['get_platform']
