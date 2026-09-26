"""Optional Gio/GTK runtime integration, no display or package tooling needed."""
import gc
from pathlib import Path
import tempfile
import time
import unittest

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gio, GLib
from lucy_diagnose.ui.file_save import ReportSaver


class FileSaveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'report.md'
        self.file = Gio.File.new_for_path(str(self.path))
        self.messages = []
        self.saver = ReportSaver(None, self.messages.append)

    def wait(self):
        deadline = time.monotonic() + 5
        while not self.messages and time.monotonic() < deadline:
            gc.collect()
            GLib.MainContext.default().iteration(False)
            time.sleep(.005)
        self.assertTrue(self.messages, 'Async operation timed out')

    def test_large_unicode_export_keeps_owned_buffer_until_complete(self):
        text = ('temperature 42 °C · local diagnostics\n' * 20000) + 'END OF REPORT'
        self.saver.write(self.file, text)
        self.wait()
        self.assertEqual(self.messages, ['File saved'])
        self.assertEqual(self.path.read_text(), text)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_existing_file_is_not_silently_overwritten(self):
        self.path.write_text('keep')
        self.saver.confirm_replace = lambda *_: self.messages.append('confirmation required')
        self.saver.write(self.file, 'replace')
        self.wait()
        self.assertEqual(self.messages, ['confirmation required'])
        self.assertEqual(self.path.read_text(), 'keep')

    def test_invalid_destination_is_reported(self):
        self.saver.write(Gio.File.new_for_path(str(self.path / 'invalid.md')), 'text')
        self.wait()
        self.assertTrue(self.messages[-1].startswith('Could not save:'))
        self.assertFalse(self.path.exists())

    def test_concurrent_edit_prevents_replacement(self):
        self.path.write_text('first')
        etag = self.file.query_info('etag::value', Gio.FileQueryInfoFlags.NONE, None).get_attribute_string('etag::value')
        time.sleep(.01)
        self.path.write_text('changed by someone else')
        self.saver.replace(self.file, 'replace', etag)
        self.wait()
        self.assertTrue(self.messages[-1].startswith('Could not save:'))
        self.assertEqual(self.path.read_text(), 'changed by someone else')
