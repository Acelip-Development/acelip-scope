"""Current public identity and preference continuity, using isolated storage."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from lucy_diagnose import __version__
from lucy_diagnose.identity import IDENTITY, DISPLAY_NAME, PUBLISHER, TAGLINE, EXECUTABLE_NAME
from lucy_diagnose.settings import SettingsStore, DEFAULTS
from lucy_diagnose.runtime import build_info
from tests.test_hardening import script

ROOT = Path(__file__).resolve().parents[1]


class CanonicalIdentityTests(unittest.TestCase):
    def test_canonical_fields(self):
        self.assertEqual(DISPLAY_NAME, 'Acelip Scope')
        self.assertEqual(PUBLISHER, 'Acelip Development')
        self.assertEqual(TAGLINE, 'System diagnostics, made clear.')
        self.assertEqual(EXECUTABLE_NAME, 'acelip-scope')
        self.assertEqual(IDENTITY['version'], __version__)
        self.assertIsNone(IDENTITY['short_name'])  # No separate abbreviated brand approved.

    def test_namespace_and_public_channels_are_unresolved(self):
        self.assertFalse(IDENTITY['application_id_finalized'])
        for key in ('repository_url', 'homepage_url', 'support_url', 'security_contact', 'license'):
            self.assertIsNone(IDENTITY[key])

    def test_cli_identity(self):
        self.assertEqual(subprocess.check_output(['python3', '-m', 'lucy_diagnose', '--version'], text=True).strip(), f'{DISPLAY_NAME} {__version__}')

    def test_readme_and_workflow_identity(self):
        self.assertTrue((ROOT/'README.md').read_text().startswith('# Acelip Scope\n'))
        self.assertIn(TAGLINE, (ROOT/'README.md').read_text())
        self.assertIn('name: acelip-scope-', (ROOT/'.github/workflows/package.yml').read_text())

    def test_no_current_ui_old_brand(self):
        for directory in ('lucy_diagnose/ui', 'lucy_diagnose/platform'):
            for p in (ROOT/directory).rglob('*.py'):
                self.assertNotIn('LUCY', p.read_text().replace('LUCY_HOST_XDG_DATA_DIRS',''), str(p))
                self.assertNotIn('LUCY Diagnose', p.read_text())

    def test_about_uses_canonical_publisher_and_tagline(self):
        text = (ROOT/'lucy_diagnose/ui/window.py').read_text()
        self.assertIn('heading=DISPLAY_NAME', text)
        self.assertIn("body=f'{TAGLINE}\\n{PUBLISHER}", text)
        self.assertEqual(build_info()['Application'], DISPLAY_NAME)
        self.assertEqual(build_info()['Publisher'], PUBLISHER)

    def test_launcher_metadata(self):
        files = script('install-user').integration_files(Path('/tmp/isolated-home'))
        launcher = next(p for p in files if p.parent.name == 'bin')
        self.assertEqual(launcher.name, EXECUTABLE_NAME)
        self.assertIn('Managed by ' + DISPLAY_NAME, files[launcher][0])
        self.assertTrue(any('Name=' + DISPLAY_NAME in data for data, _ in files.values()))


class PreferenceMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old = self.root/'lucy-diagnose/preferences.json'
        self.new = self.root/'acelip-scope/preferences.json'
        self.old.parent.mkdir()
        self.choices = dict(theme='arcanum', live_graphs=False, report_privacy='local')

    def load(self):
        store = SettingsStore(self.new, legacy_path=self.old)
        self.addCleanup(store.close)
        return store

    def seed(self):
        self.old.write_text(json.dumps(self.choices))

    def test_neither_file_means_defaults_without_write(self):
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertFalse(self.new.exists())

    def test_migrates_all_compatible_choices_once(self):
        self.seed()
        self.assertEqual(self.load().values, self.choices)
        self.assertEqual(json.loads(self.new.read_text()), self.choices)
        self.assertEqual(self.new.stat().st_mode & 0o777, 0o600)
        self.assertFalse(self.old.exists())
        self.assertEqual(self.load().values, self.choices)

    def test_existing_new_settings_win(self):
        self.seed(); self.new.parent.mkdir()
        self.new.write_text(json.dumps(DEFAULTS))
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertTrue(self.old.exists())

    def test_invalid_new_is_not_overwritten(self):
        self.seed(); self.new.parent.mkdir(); self.new.write_text('bad')
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertEqual(self.new.read_text(), 'bad')

    def test_invalid_old_json_is_retained(self):
        self.old.write_text('bad')
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertFalse(self.new.exists())
        self.assertTrue(self.old.exists())

    def test_nonobject_old_is_not_imported(self):
        self.old.write_text('[]')
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertFalse(self.new.exists())

    def test_unknown_and_invalid_choices_use_safe_defaults(self):
        self.old.write_text(json.dumps(dict(theme='invalid', live_graphs='yes', report_privacy='invalid', ai_consent=True)))
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertEqual(json.loads(self.new.read_text()), DEFAULTS)

    def test_failed_write_keeps_legacy_preferences_and_retries(self):
        self.seed()
        with patch('lucy_diagnose.settings.os.link', side_effect=PermissionError):
            store = self.load()
        self.assertEqual(store.values, self.choices)
        self.assertEqual(store.migration, 'retry needed')
        self.assertTrue(self.old.exists())
        self.assertFalse(self.new.exists())
        self.assertEqual(self.load().migration, 'migrated')

    def test_concurrently_created_new_file_wins(self):
        self.seed()
        def race(*args):
            self.new.write_text(json.dumps(DEFAULTS))
            raise FileExistsError
        with patch('lucy_diagnose.settings.os.link', side_effect=race):
            self.assertEqual(self.load().values, DEFAULTS)
        self.assertTrue(self.old.exists())

    def test_legacy_symlink_is_not_imported(self):
        target = self.root/'target';target.write_text(json.dumps(self.choices))
        self.old.symlink_to(target)
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertTrue(self.old.is_symlink())

    def test_dangling_new_symlink_is_preserved(self):
        self.seed(); self.new.parent.mkdir(); self.new.symlink_to(self.root/'absent')
        self.assertEqual(self.load().values, DEFAULTS)
        self.assertTrue(self.new.is_symlink())
        self.assertTrue(self.old.exists())

    def test_automatic_packaged_path_detection(self):
        self.seed()
        with patch('lucy_diagnose.settings.PREFERENCES_PATH', self.new):
            store = SettingsStore(self.new)
        self.addCleanup(store.close)
        self.assertEqual(store.values, self.choices)
        self.assertEqual(store.migration, 'migrated')

    def test_native_preferences_stay_in_place(self):
        self.seed()
        store = SettingsStore(self.old)
        self.addCleanup(store.close)
        self.assertEqual(store.values, self.choices)
        self.assertTrue(self.old.exists())
        self.assertEqual(store.migration, 'not needed')
