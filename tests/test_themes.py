import json
from pathlib import Path
import tempfile
import unittest

from lucy_diagnose.settings import SettingsStore, validated
from lucy_diagnose.themes.catalog import (CATEGORIES, DEFAULT_THEME, GRAPH_LIMITS, THEMES,
                                        SEVERITY_ICONS, graph_color, graph_state, palette, rgb)
from lucy_diagnose.themes.manager import ThemeManager


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'preferences.json'
        self.stores = []

    def tearDown(self):
        for store in self.stores:
            store.close()
        self.tmp.cleanup()

    def store(self):
        store = SettingsStore(self.path)
        self.stores.append(store)
        return store

    def test_first_launch_system_without_writing_preferences(self):
        self.assertEqual(DEFAULT_THEME, 'system')
        self.assertEqual(ThemeManager(self.store()).current, 'system')
        self.assertFalse(self.path.exists())

    def test_missing_preference_system(self):
        self.path.write_text('{}')
        self.assertEqual(self.store().get('theme'), 'system')

    def test_invalid_removed_and_malformed_preference_system(self):
        for value in ('removed-theme', 2, None, [], {}):
            self.assertEqual(validated({'theme': value})['theme'], 'system')
        self.path.write_text('{broken')
        self.assertEqual(self.store().get('theme'), 'system')

    def test_corrupt_unrelated_preferences_do_not_discard_valid_theme(self):
        for privacy in ([], {}, None, 1):
            self.path.write_text(json.dumps({'theme': 'arcanum', 'report_privacy': privacy, 'live_graphs': 'bad'}))
            store = self.store()
            self.assertEqual(store.get('theme'), 'arcanum')
            self.assertEqual(store.get('report_privacy'), 'sanitized')
            self.assertTrue(store.get('live_graphs'))

    def test_arcanum_selectable_and_restored(self):
        store = self.store()
        manager = ThemeManager(store)
        manager.select('Arcanum')
        store.flush()
        self.assertEqual(manager.current, 'arcanum')
        self.assertEqual(ThemeManager(self.store()).current, 'arcanum')

    def test_all_builtins_restore_and_have_complete_graph_palettes(self):
        self.assertEqual(len(THEMES), 13)
        for key in THEMES:
            self.path.write_text(json.dumps({'theme': key}))
            manager = ThemeManager(self.store())
            self.assertEqual(manager.current, key)
            for metric in GRAPH_LIMITS:
                self.assertEqual(len(rgb(graph_color(manager.colors, metric))), 3)
            for severity in SEVERITY_ICONS:
                self.assertTrue(SEVERITY_ICONS[severity])
                if severity != 'unavailable':
                    self.assertIn(severity, manager.colors)

    def test_runtime_switch_notifies_backend_and_graph_listeners(self):
        class Backend:
            dark = False
            accent = '#123456'
            def apply(self, key):
                self.current = key
        backend = Backend()
        manager = ThemeManager(self.store(), backend)
        changes = []
        manager.listeners.append(lambda: changes.append(manager.colors))
        for key in THEMES:
            manager.select(key)
            self.assertEqual(backend.current, key)
        self.assertEqual(len(changes), 13)

    def test_system_palette_follows_host_dark_and_accent(self):
        self.assertNotEqual(palette('system', False)['background'], palette('system', True)['background'])
        self.assertEqual(palette('system', True, '#123456')['primary'], '#123456')
        self.assertNotEqual(palette('system')['primary'], palette('arcanum')['primary'])

    def test_categories_and_arcanum_identity(self):
        self.assertEqual(CATEGORIES, ('System', 'Signature', 'Workstation', 'Creative'))
        self.assertEqual(THEMES['arcanum'].category, 'Signature')
        self.assertEqual(THEMES['arcanum'].colors['primary'], '#ef79dc')

    def test_invalid_runtime_switch_falls_back_system(self):
        manager = ThemeManager(self.store())
        manager.select('arcanum')
        manager.select('removed')
        self.assertEqual(manager.current, 'system')

    def test_paused_missing_and_thresholds_have_text(self):
        self.assertIn('PAUSED', graph_state('cpu', 100, True)[1])
        self.assertEqual(graph_state('cpu_temp', None)[0], 'unavailable')
        self.assertEqual(graph_state('gpu_temp', 96)[0], 'error')
        self.assertEqual(graph_state('ram', 95)[0], 'warning')
        self.assertEqual(graph_state('cpu', 100)[0], 'info')

    def test_rapid_preference_updates_persist_latest(self):
        store = self.store()
        for i in range(200):
            store.set('theme', 'arcanum' if i % 2 else 'system')
        store.set('theme', 'ion')
        store.flush()
        self.assertEqual(json.loads(self.path.read_text())['theme'], 'ion')
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(set(json.loads(self.path.read_text())), {'theme', 'live_graphs', 'report_privacy'})
