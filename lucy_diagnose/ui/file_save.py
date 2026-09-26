"""Portal-backed selection and explicit, race-aware report replacement."""
from gi.repository import Adw, Gio, GLib, Gtk


class ReportSaver:
    def __init__(self, window, notify):
        self.window, self.notify = window, notify

    def choose(self, text, name, cancellable=None):
        chooser = Gtk.FileDialog(title='Save reviewed report or analysis', initial_name=name)
        def selected(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    self.write(file, text)
            except GLib.Error as exc:
                if not (exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED) or
                        exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.CANCELLED) or
                        exc.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED)):
                    self.notify('Could not save: ' + exc.message)
        chooser.save(self.window, cancellable, selected)
        return chooser

    def write(self, file, text):
        def created(file, result):
            try:
                stream = file.create_finish(result)
            except GLib.Error as exc:
                if exc.matches(Gio.io_error_quark(), Gio.IOErrorEnum.EXISTS):
                    self.confirm_replace(file, text)
                else:
                    self.notify('Could not save: ' + exc.message)
                return
            def written(stream, result):
                try:
                    stream.write_all_finish(result)
                except GLib.Error as exc:
                    self.notify('Could not save: ' + exc.message)
                    stream.close_async(GLib.PRIORITY_DEFAULT, None, None)
                    return
                def closed(stream, result):
                    try:
                        stream.close_finish(result)
                        self.notify('File saved')
                    except GLib.Error as exc:
                        self.notify('Could not save: ' + exc.message)
                stream.close_async(GLib.PRIORITY_DEFAULT, None, closed)
            stream.write_all_async(text.encode(), GLib.PRIORITY_DEFAULT, None, written)
        file.create_async(Gio.FileCreateFlags.PRIVATE, GLib.PRIORITY_DEFAULT, None, created)

    def confirm_replace(self, file, text):
        # Query an etag before asking: concurrent edits must not be overwritten.
        def inspected(file, result):
            try:
                etag = file.query_info_finish(result).get_attribute_string('etag::value')
                if not etag:
                    self.notify('Could not safely replace this file; choose a new filename')
                    return
            except GLib.Error as exc:
                self.notify('Could not save: ' + exc.message)
                return
            dialog = Adw.AlertDialog(heading='Replace existing file?', body='This file already exists. Replace it with the reviewed report?')
            dialog.add_response('cancel', 'Cancel')
            dialog.add_response('replace', 'Replace')
            dialog.set_response_appearance('replace', Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response('cancel')
            dialog.set_close_response('cancel')
            def chosen(dialog, result):
                if dialog.choose_finish(result) == 'replace':
                    self.replace(file, text, etag)
            dialog.choose(self.window, None, chosen)
        file.query_info_async('etag::value', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                              GLib.PRIORITY_DEFAULT, None, inspected)

    def replace(self, file, text, etag):
        def saved(file, result):
            try:
                file.replace_contents_finish(result)
                self.notify('File saved')
            except GLib.Error as exc:
                self.notify('Could not save: ' + exc.message)
        file.replace_contents_bytes_async(GLib.Bytes.new(text.encode()), etag, False,
            Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION, None, saved)
