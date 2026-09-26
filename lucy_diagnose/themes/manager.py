"""Runtime theme selection; no global GNOME settings or telemetry."""

from .catalog import THEMES, normalize_theme, palette


class ThemeManager:
    def __init__(self, settings, backend=None):
        self.settings = settings
        self.backend = backend
        self.current = normalize_theme(settings.get('theme'))
        self.listeners = []
        if backend:
            backend.apply(self.current)

    @property
    def colors(self):
        return palette(self.current, getattr(self.backend, 'dark', False), getattr(self.backend, 'accent', None))

    @property
    def theme(self):
        return THEMES[self.current]

    def select(self, name, persist=True):
        self.current = normalize_theme(name)
        if self.backend:
            self.backend.apply(self.current)
        if persist:
            self.settings.set('theme', self.current)
        self.notify()

    def notify(self):
        for listener in list(self.listeners):
            listener()
