"""Approved namespace is separate from remote availability and sandbox state."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from lucy_diagnose.identity import APP_ID, DEVELOPER_ID, IDENTITY, planned_urls, public_urls
from lucy_diagnose.settings import SettingsStore, DEFAULTS
from tests.test_hardening import script

ROOT = Path(__file__).resolve().parents[1]
metadata = script('render-metadata')
packaging = script('package')
checklist = script('release-checklist')
migration = script('migrate-flatpak-preferences')


class NamespaceTests(unittest.TestCase):
    def test_final_canonical_ids(self):
        self.assertEqual(APP_ID,'io.github.acelip_development.acelip-scope')
        self.assertEqual(DEVELOPER_ID,'io.github.acelip_development')
        self.assertTrue(IDENTITY['application_id_finalized'])

    def test_appstream_developer_and_launchable(self):
        root=ET.parse(ROOT/'data'/f'{APP_ID}.metainfo.xml').getroot()
        self.assertEqual(root.findtext('id'),APP_ID)
        self.assertEqual(root.find('developer').get('id'),DEVELOPER_ID)
        self.assertEqual(root.findtext('developer/name'),'Acelip Development')
        self.assertEqual(root.findtext('launchable'),APP_ID+'.desktop')
        self.assertIsNone(root.find('url'))

    def test_manifest_and_desktop_filenames(self):
        self.assertEqual(packaging.MANIFEST.name,APP_ID+'.json')
        self.assertEqual(json.loads(packaging.MANIFEST.read_text())['app-id'],APP_ID)
        self.assertEqual({p.name for p in (ROOT/'data').glob('*.desktop')},{APP_ID+'.desktop'})
        self.assertEqual({p.name for p in (ROOT/'data').glob('*.metainfo.xml')},{APP_ID+'.metainfo.xml'})

    def test_staged_resources_and_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            packaging.stage(Path(d),'Flatpak')
            prefix=Path(d)/'share'
            self.assertTrue((prefix/'icons/hicolor/scalable/apps'/f'{APP_ID}.svg').is_file())
            self.assertTrue((prefix/'applications'/f'{APP_ID}.desktop').is_file())
            data=json.loads((prefix/'acelip-scope/lucy_diagnose/_build.json').read_text())
            self.assertEqual(data['application_id'],APP_ID)
            self.assertEqual(data['developer_id'],DEVELOPER_ID)
            for p in Path(d).rglob('*'):
                if p.is_file():
                    self.assertNotIn(migration.PREVIOUS_APP_ID.encode(),p.read_bytes(),str(p.relative_to(d)))

    def test_repository_and_support_targets_are_centralized(self):
        targets=planned_urls()
        self.assertEqual(IDENTITY['repository_namespace'],'Acelip-Development/acelip-scope')
        self.assertEqual(targets['repository_url'],'https://github.com/Acelip-Development/acelip-scope')
        self.assertEqual(targets['homepage_url'],targets['repository_url'])
        self.assertEqual(targets['support_url'],targets['repository_url']+'/issues')

    def test_targets_do_not_automatically_become_public_links(self):
        self.assertEqual(public_urls(),dict(repository_url=None,homepage_url=None,support_url=None))
        self.assertFalse(IDENTITY['remote_repository_created'])
        for text in metadata.rendered().values():
            self.assertNotIn(IDENTITY['repository_url'],text)

    def test_reachable_flags_without_repository_do_not_publish_links(self):
        state={**IDENTITY,'homepage_reachable':True,'support_reachable':True}
        self.assertTrue(all(v is None for v in public_urls(state).values()))

    def test_created_repository_does_not_prove_homepage_or_issues(self):
        state={**IDENTITY,'remote_repository_created':True}
        self.assertEqual(public_urls(state)['repository_url'],IDENTITY['repository_url'])
        self.assertIsNone(public_urls(state)['homepage_url'])
        self.assertIsNone(public_urls(state)['support_url'])

    def test_verified_future_links_use_the_approved_target(self):
        state={**IDENTITY,'remote_repository_created':True,'homepage_reachable':True,'support_reachable':True}
        self.assertEqual(public_urls(state),planned_urls(state))

    def test_checklist_distinguishes_preparation_from_remote_facts(self):
        gates={g['gate']:g for g in checklist.evaluate(IDENTITY,{})}
        for name in ['Application ID','Developer ID','Target repository namespace']:
            self.assertEqual(gates[name]['status'],'PASS')
        for name in ['Remote repository created','Homepage reachable','Support/issues reachable','Security reporting configured','CI green on GitHub','Bundled-runtime advisory/source-obligation review']:
            self.assertEqual(gates[name]['status'],'BLOCKED')

    def test_final_id_is_valid_for_gapplication(self):
        from gi.repository import Gio
        self.assertTrue(Gio.Application.id_is_valid(APP_ID))


class FlatpakPreferenceMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.final,(self.provisional,self.legacy)=migration.paths(self.home)
        self.choices=dict(theme='mauveglass',report_privacy='local',live_graphs=False)

    def seed(self,path,values):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(values))

    def test_full_old_to_provisional_to_final_chain(self):
        self.seed(self.legacy,self.choices)
        initial=SettingsStore(self.provisional,legacy_path=self.legacy)
        self.assertEqual(initial.values,self.choices);initial.close()
        self.assertFalse(self.legacy.exists())
        self.assertIn('migrated',migration.migrate(self.home))
        final=SettingsStore(self.final)
        self.assertEqual(final.values,self.choices);final.close()
        self.assertTrue(self.provisional.exists())
        self.assertEqual(self.final.stat().st_mode & 0o777,0o600)

    def test_direct_old_to_final_skips_missing_intermediate(self):
        self.seed(self.legacy,self.choices)
        migration.migrate(self.home)
        self.assertEqual(json.loads(self.final.read_text()),self.choices)
        self.assertTrue(self.legacy.exists())

    def test_provisional_wins_over_older_settings(self):
        self.seed(self.legacy,DEFAULTS);self.seed(self.provisional,self.choices)
        migration.migrate(self.home)
        self.assertEqual(json.loads(self.final.read_text()),self.choices)

    def test_existing_final_settings_and_repeat_runs_are_unchanged(self):
        self.seed(self.provisional,self.choices);self.seed(self.final,DEFAULTS)
        before=self.final.read_bytes()
        for _ in range(2):self.assertIn('preserved',migration.migrate(self.home))
        self.assertEqual(self.final.read_bytes(),before)
        self.assertEqual(json.loads(self.provisional.read_text()),self.choices)

    def test_dry_run_does_not_create_destination(self):
        self.seed(self.provisional,self.choices)
        self.assertIn('no files changed',migration.migrate(self.home,True))
        self.assertFalse(self.final.exists())

    def test_neither_old_store_means_system_defaults(self):
        self.assertIn('System defaults',migration.migrate(self.home))
        store=SettingsStore(self.final);self.assertEqual(store.values,DEFAULTS);store.close()
        self.assertFalse(self.final.exists())

    def test_invalid_newer_source_does_not_resurrect_older_preferences(self):
        self.seed(self.legacy,self.choices);self.seed(self.provisional,[])
        with self.assertRaises(ValueError):migration.migrate(self.home)
        self.assertFalse(self.final.exists());self.assertTrue(self.legacy.exists())

    def test_failed_write_preserves_sources(self):
        self.seed(self.provisional,self.choices)
        with patch('lucy_diagnose.settings.os.link',side_effect=PermissionError):
            with self.assertRaises(OSError):migration.migrate(self.home)
        self.assertTrue(self.provisional.exists());self.assertFalse(self.final.exists())

    def test_concurrent_destination_creation_wins(self):
        self.seed(self.provisional,self.choices)
        def race(*args):
            self.final.write_text(json.dumps(DEFAULTS));raise FileExistsError
        with patch('lucy_diagnose.settings.os.link',side_effect=race):
            self.assertIn('Concurrently',migration.migrate(self.home))
        self.assertEqual(json.loads(self.final.read_text()),DEFAULTS)
        self.assertTrue(self.provisional.exists())

    def test_symlinked_source_parent_is_rejected(self):
        outside=self.home/'elsewhere';outside.mkdir()
        self.provisional.parent.parent.mkdir(parents=True)
        self.provisional.parent.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):migration.migrate(self.home)
        self.assertFalse(self.final.exists())

    def test_symlinked_destination_parent_is_rejected(self):
        self.seed(self.provisional,self.choices)
        outside=self.home/'elsewhere';outside.mkdir()
        self.final.parent.parent.mkdir(parents=True)
        self.final.parent.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):migration.migrate(self.home)
        self.assertFalse((outside/'preferences.json').exists())

    def test_ai_consent_and_obsolete_keys_are_never_copied(self):
        self.seed(self.provisional,{**self.choices,'ai_consent':True,'old_ui_key':'obsolete'})
        migration.migrate(self.home)
        self.assertEqual(json.loads(self.final.read_text()),self.choices)
