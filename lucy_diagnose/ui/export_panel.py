import copy
import logging
import threading
from gi.repository import GLib, Gtk
from ..exports import prepare_export
from .widgets import set_expander_content, accessible_name, box, label, text_view


class ExportPanel(Gtk.Expander):
    def __init__(self, window):
        super().__init__(label='Export report · Markdown / JSON')
        self.window, self.prepared, self.generation = window, None, 0
        self.busy = False
        body = box()
        set_expander_content(self, body)
        body.append(label('Review the exact contents below before saving. Both privacy levels remove recognized secrets; sanitized also masks common identifiers. Nothing is saved automatically.', None, True))
        actions = box(Gtk.Orientation.HORIZONTAL, 8)
        self.format = Gtk.DropDown.new_from_strings(('Markdown', 'JSON'))
        accessible_name(self.format, 'Report format')
        self.privacy = Gtk.DropDown.new_from_strings(('Sanitized · recommended', 'Local details · secrets removed'))
        accessible_name(self.privacy, 'Export privacy level')
        self.privacy.set_selected(0 if window.get_application().settings.get('report_privacy') == 'sanitized' else 1)
        for dropdown in (self.format, self.privacy):
            dropdown.connect('notify::selected', lambda *_: self.invalidate())
            actions.append(dropdown)
        self.prepare = Gtk.Button(label='Prepare preview')
        self.prepare.connect('clicked', lambda _: self.build_preview())
        actions.append(self.prepare)
        body.append(actions)
        self.status = label('No export prepared', 'caption', True)
        body.append(self.status)
        scroll, self.preview = text_view(height=300)
        body.append(scroll)
        self.save = Gtk.Button(label='Save reviewed report…', sensitive=False, halign=Gtk.Align.START)
        self.save.connect('clicked', lambda _: window.save_text(*self.prepared) if self.prepared else None)
        body.append(self.save)

    def invalidate(self):
        self.generation += 1
        self.prepared = None
        self.save.set_sensitive(False)
        self.preview.get_buffer().set_text('')
        self.status.set_text('Prepare a new preview for the current observations and options')

    def build_preview(self):
        if self.busy:
            return
        self.invalidate()
        state = copy.deepcopy(self.window.state)
        format = 'json' if self.format.get_selected() else 'markdown'
        privacy = 'local' if self.privacy.get_selected() else 'sanitized'
        generation = self.generation
        self.busy = True
        self.prepare.set_sensitive(False)
        self.status.set_text('Preparing a filtered copy in the background…')
        def worker():
            try:
                prepared = prepare_export(state, format, privacy)
            except Exception as exc:
                logging.getLogger(__name__).warning('Export preparation failed (%s)', type(exc).__name__)
                prepared = None
            GLib.idle_add(self.ready, generation, prepared)
        threading.Thread(target=worker, daemon=True, name='lucy-export').start()

    def ready(self, generation, prepared):
        if self.window.closed:
            return False
        self.busy = False
        self.prepare.set_sensitive(True)
        if generation != self.generation:
            return False
        self.prepared = prepared
        self.save.set_sensitive(prepared is not None)
        if prepared:
            self.preview.get_buffer().set_text(prepared[0])
            self.status.set_text(f'{prepared[1]} · preview only · not saved')
        else:
            self.status.set_text('Could not prepare export; no file was saved')
        return False
