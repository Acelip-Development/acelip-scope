from pathlib import Path
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_foreign('cairo')
from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

APP_ID = 'io.github.lucydiagnose.LucyDiagnose'


class LucyApplication(Adw.Application):
    def __init__(self, smoke_test=False):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE if smoke_test else Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.smoke_test = smoke_test
        self.smoke_passed = False

    def do_activate(self):
        if self.get_active_window():
            self.get_active_window().present()
            return
        # Per-application preference only; never changes GNOME settings.
        self.get_style_manager().set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        provider = Gtk.CssProvider()
        provider.load_from_path(str(Path(__file__).with_name('style.css')))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        from .window import LucyWindow
        window = LucyWindow(self)
        window.present()
