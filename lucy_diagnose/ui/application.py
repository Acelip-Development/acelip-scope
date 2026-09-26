import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_foreign('cairo')
from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402
from ..settings import SettingsStore, PREFERENCES_PATH
from ..themes.manager import ThemeManager
from ..themes.gtk_backend import GtkThemeBackend

from ..runtime import APP_ID


class LucyApplication(Adw.Application):
    def __init__(self, smoke_test=False):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE if smoke_test else Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.smoke_test = smoke_test
        self.smoke_passed = False

    def do_activate(self):
        if self.get_active_window():
            self.get_active_window().present()
            return
        path = getattr(self, 'preferences_path', PREFERENCES_PATH if not self.smoke_test else PREFERENCES_PATH.with_name('smoke-preferences.json'))
        self.settings = SettingsStore(path)
        if self.smoke_test:
            self.settings.values['live_graphs'] = True
        backend = GtkThemeBackend(self.get_style_manager())
        self.themes = ThemeManager(self.settings, backend)
        backend.changed = self.themes.notify
        from .window import LucyWindow
        window = LucyWindow(self)
        window.present()
