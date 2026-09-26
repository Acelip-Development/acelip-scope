"""Inline preferences: local settings, never host desktop settings."""
from ..identity import DISPLAY_NAME, PUBLISHER, TAGLINE, LICENSE, COPYRIGHT
from ..runtime import detect_runtime
from gi.repository import Adw, Gtk
import platform

from .. import __version__
from ..themes.catalog import CATEGORIES, THEMES
from .widgets import set_expander_content, accessible_name, box, label, padded


class PreferencesPanel(Gtk.Expander):
    def __init__(self, window):
        super().__init__(label='Preferences')
        self.window = window
        self.settings = window.get_application().settings
        self.themes = window.get_application().themes
        body = box(spacing=18)
        set_expander_content(self, body)
        appearance = Adw.PreferencesGroup(title='Appearance')
        row = Adw.ActionRow(title='Theme', subtitle='System follows the desktop appearance exposed by GTK; changes apply immediately.')
        self.theme_button = Gtk.MenuButton(valign=Gtk.Align.CENTER)
        accessible_name(self.theme_button, 'Choose theme')
        self.popover = Gtk.Popover()
        choices = padded(box(spacing=5), 8)
        self.theme_choices = {}
        group = None
        for category in CATEGORIES:
            choices.append(label(category, 'theme-category'))
            for key, theme in THEMES.items():
                if theme.category != category:
                    continue
                button = Gtk.CheckButton(label=theme.name + (' · DEFAULT' if key == 'system' else ''))
                if group is not None:
                    button.set_group(group)
                group = button
                button.set_active(key == self.themes.current)
                button.connect('toggled', self.select_theme, key)
                choices.append(button)
                self.theme_choices[key] = button
        self.popover.set_child(choices)
        self.theme_button.set_popover(self.popover)
        row.add_suffix(self.theme_button)
        appearance.add(row)
        body.append(appearance)
        self.themes.listeners.append(self.theme_changed)
        self.theme_changed()
        diagnostics = Adw.PreferencesGroup(title='Diagnostics')
        self.live = Adw.SwitchRow(title='Live graphs', subtitle='Lightweight metrics every 2 seconds; history stays in memory.', active=window.live_toggle.get_active())
        self.live.connect('notify::active', lambda row, _: window.live_toggle.set_active(row.get_active()))
        window.live_toggle.connect('toggled', lambda toggle: self.live.set_active(toggle.get_active()))
        diagnostics.add(self.live)
        privacy = Adw.ActionRow(title='Report privacy', subtitle='Default for export previews. External AI always receives sanitized text.')
        self.privacy = Gtk.DropDown.new_from_strings(('Sanitized · recommended', 'Local details · secrets removed'))
        accessible_name(self.privacy, 'Default report privacy')
        self.privacy.set_selected(0 if self.settings.get('report_privacy') == 'sanitized' else 1)
        self.privacy.set_valign(Gtk.Align.CENTER)
        self.privacy.connect('notify::selected', lambda row, _: self.settings.set('report_privacy', 'local' if row.get_selected() else 'sanitized'))
        privacy.add_suffix(self.privacy)
        diagnostics.add(privacy)
        body.append(diagnostics)
        ai = Adw.PreferencesGroup(title='AI')
        row = Adw.ActionRow(title='Explicit consent for every handoff', subtitle='Codex / Claude: External, sanitized preview. Ollama: Local. Commands are prepared only; Acelip Scope never runs them.')
        row.set_subtitle_lines(0)
        action = Gtk.Button(label='Review analysis', valign=Gtk.Align.CENTER)
        action.connect('clicked', lambda _: window.open_analysis())
        row.add_suffix(action)
        ai.add(row)
        body.append(ai)
        about = Adw.PreferencesGroup(title='About')
        about.add(Adw.ActionRow(title=DISPLAY_NAME + ' ' + __version__, subtitle=f'Native GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()} · libadwaita {Adw.get_major_version()}.{Adw.get_minor_version()} · Python {platform.python_version()} · {detect_runtime().package} runtime'))
        about.add(Adw.ActionRow(title=PUBLISHER, subtitle=TAGLINE))
        about.add(Adw.ActionRow(title='Read-only diagnostics', subtitle='No repairs, package installation, service changes, telemetry, or diagnostic history. Preferences stay in local application storage.'))
        about.add(Adw.ActionRow(title='License: ' + LICENSE, subtitle=COPYRIGHT + '. Third-party components retain their respective licenses.'))
        body.append(about)

    def select_theme(self, button, key):
        if button.get_active() and key != self.themes.current:
            self.themes.select(key)
            self.popover.popdown()

    def theme_changed(self):
        self.theme_button.set_label(self.themes.theme.name)
        self.theme_choices[self.themes.current].set_active(True)
