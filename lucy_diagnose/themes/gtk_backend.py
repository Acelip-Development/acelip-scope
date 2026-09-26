from pathlib import Path
from gi.repository import Adw, Gdk, Gtk

from .catalog import THEMES, palette


class GtkThemeBackend:
    def __init__(self, style_manager):
        self.style = style_manager
        self.provider = Gtk.CssProvider()
        self.base_css = Path(__file__).with_name('base.css').read_text()
        self.current = 'system'
        self.busy = False
        self.changed = None
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.style.connect('notify::dark', self.system_changed)
        if hasattr(self.style, 'get_accent_color_rgba'):
            self.style.connect('notify::accent-color', self.system_changed)

    @property
    def dark(self):
        return self.style.get_dark()

    @property
    def accent(self):
        if hasattr(self.style, 'get_accent_color_rgba'):
            color = self.style.get_accent_color_rgba()
            return '#' + ''.join(f'{round(v * 255):02x}' for v in (color.red, color.green, color.blue))
        return None

    def apply(self, theme_id):
        self.busy = True
        self.current = theme_id
        theme = THEMES[theme_id]
        self.style.set_color_scheme({'system': Adw.ColorScheme.DEFAULT, 'dark': Adw.ColorScheme.FORCE_DARK,
                                     'light': Adw.ColorScheme.FORCE_LIGHT}[theme.mode])
        colors = palette(theme_id, self.dark, self.accent)
        definitions = [f'@define-color lucy_{key} {value};' for key, value in colors.items()]
        if theme.mode != 'system':
            for target, source in {'window_bg_color': 'background', 'window_fg_color': 'text', 'view_bg_color': 'background',
                                   'view_fg_color': 'text', 'card_bg_color': 'panel', 'card_fg_color': 'text',
                                   'headerbar_bg_color': 'background', 'headerbar_fg_color': 'text',
                                   'popover_bg_color': 'elevated', 'popover_fg_color': 'text', 'dialog_bg_color': 'panel',
                                   'dialog_fg_color': 'text', 'accent_bg_color': 'accent_bg', 'accent_color': 'primary'}.items():
                definitions.append(f'@define-color {target} {colors[source]};')
            definitions.append('@define-color accent_fg_color #ffffff;')
        self.provider.load_from_string('\n'.join(definitions) + '\n' + self.base_css)
        self.busy = False

    def system_changed(self, *_):
        if not self.busy and self.current == 'system':
            self.apply(self.current)
            if self.changed:
                self.changed()
