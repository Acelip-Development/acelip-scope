"""Packaging regression tests: no GTK, network, Flatpak or AppImage tools required."""
import configparser
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import xml.etree.ElementTree as ET

from lucy_diagnose import __version__
from lucy_diagnose.identity import IDENTITY
from lucy_diagnose.runtime import APP_ID, Runtime, detect_runtime, state_directory, build_info, render_build_info
from lucy_diagnose.models import Support, Status
from lucy_diagnose.platform.linux import sandbox
from lucy_diagnose.platform.linux.backend import LinuxPlatform
from lucy_diagnose.platform.linux.capabilities import Capabilities
from lucy_diagnose.platform.linux.common import unavailable
from lucy_diagnose.platform.linux.runner import Runner
from lucy_diagnose.platform.linux.storage import device_health
from lucy_diagnose.platform.linux.packages import Packages
from lucy_diagnose.platform.linux.services import Services
from lucy_diagnose.commands import Result

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_script', ROOT / 'scripts/package.py')
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)


class RuntimeTests(unittest.TestCase):
    def detect(self, env, info=False):
        return detect_runtime(env, Mock(is_file=Mock(return_value=info)))

    def test_native(self):
        self.assertEqual(self.detect({}), Runtime('Native'))

    def test_flatpak_environment(self):
        self.assertTrue(self.detect({'FLATPAK_ID': APP_ID}).restricted)

    def test_flatpak_marker(self):
        self.assertEqual(self.detect({}, True).package, 'Flatpak')

    def test_empty_flatpak_id_is_not_detection(self):
        self.assertEqual(self.detect({'FLATPAK_ID': ''}).package, 'Native')

    def test_appimage_runtime(self):
        self.assertEqual(self.detect({'APPIMAGE': '/tmp/test.AppImage'}).package, 'AppImage')

    def test_extracted_appimage(self):
        self.assertEqual(self.detect({'APPDIR': '/tmp/squashfs-root'}).package, 'AppImage')

    def test_flatpak_takes_precedence(self):
        self.assertEqual(self.detect({'APPDIR': '/tmp/app'}, True).package, 'Flatpak')

    def test_appimage_is_not_a_sandbox(self):
        self.assertFalse(self.detect({'APPIMAGE': '/tmp/a'}).restricted)

    def test_packaged_config_outside_bundle(self):
        self.assertEqual(state_directory('config', {'XDG_CONFIG_HOME': '/tmp/config'}, Runtime('AppImage')), Path('/tmp/config/acelip-scope'))

    def test_flatpak_respects_remapped_xdg(self):
        self.assertEqual(state_directory('state', {'XDG_STATE_HOME': '/tmp/flatpak/state'}, Runtime('Flatpak', True)), Path('/tmp/flatpak/state/acelip-scope'))

    def test_relative_xdg_is_ignored(self):
        self.assertTrue(state_directory('config', {'XDG_CONFIG_HOME': 'relative'}, Runtime('AppImage')).is_absolute())

    def test_provenance_rendering(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'metadata.json'
            p.write_text(json.dumps({'commit': 'a' * 40, 'runtime': 'GNOME 50', 'dirty': False}))
            text = render_build_info(runtime=Runtime('Flatpak', True), metadata_path=p, platform_name='Linux')
            for value in (__version__, 'a' * 40, 'Flatpak', 'GNOME 50', 'Restricted', 'Linux'):
                self.assertIn(value, text)
            self.assertNotIn(d, text)

    def test_provenance_drops_path_injected_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'metadata.json'
            p.write_text(json.dumps({'commit': '/home/person/private', 'runtime': '/home/person/runtime'}))
            self.assertNotIn('/home/', render_build_info(metadata_path=p))

    def test_invalid_metadata_fails_safe(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.json'
            p.write_text('[]')
            self.assertEqual(build_info(metadata_path=p)['Source state'], 'Unstamped')


class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('lucy_diagnose.platform.linux.sandbox.restricted', return_value=True)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_sandbox_restriction_is_not_error(self):
        result = Runner().run('smartctl', '--all', '/dev/sda')
        check = unavailable('SMART', result)
        self.assertEqual(check.support, Support.UNAVAILABLE)
        self.assertEqual(check.status, Status.UNAVAILABLE)
        self.assertIn(sandbox.RESTRICTION, check.summary)

    def test_absolute_command_paths_cannot_bypass_mapping(self):
        self.assertIn(sandbox.RESTRICTION, Runner().run('/usr/bin/systemctl', '--failed').problem)

    def test_capability_discovery_does_not_claim_host_command(self):
        which = Mock(return_value='/usr/bin/smartctl')
        capability = Capabilities(which=which).find_command('smartctl')
        self.assertFalse(capability.available)
        which.assert_not_called()

    def test_host_packages_are_unknown_not_absent(self):
        item = Packages().find('discord')[0]
        self.assertIsNone(item.installed)
        self.assertIn(sandbox.RESTRICTION, item.evidence)

    def test_host_services_are_unavailable_not_failed(self):
        item = Services().get('wireplumber.service', 'user')
        self.assertEqual(item.support, Support.UNAVAILABLE)
        self.assertNotEqual(item.state, 'FAILED')

    def test_host_collectors_do_not_probe_hidden_host(self):
        runner = Mock()
        for mode in ('Storage', 'Network', 'AI Stack'):
            for collect in LinuxPlatform().scan_jobs(mode).values():
                checks = collect(runner)
                self.assertTrue(checks)
                self.assertTrue(all(c.support == Support.UNAVAILABLE and c.status != Status.ERROR for c in checks))
        runner.run.assert_not_called()

    def test_flatpak_sharing_preserves_unverified_capture(self):
        with patch.object(sandbox, 'portal_capability', return_value=sandbox.limitation('ScreenCast portal')):
            checks = sandbox.collect('Discord / Screen Sharing', Mock())
        self.assertTrue(any('unverified' in c.summary for c in checks))
        self.assertFalse(any(c.status == Status.ERROR for c in checks))

    def test_native_command_discovery_retains_host_access(self):
        with patch.object(sandbox, 'restricted', return_value=False):
            self.assertTrue(Capabilities(which=lambda _: '/usr/bin/smartctl').find_command('smartctl').available)

    def test_smart_sandbox_distinct_from_missing_tool(self):
        check = device_health(Runner(), {'path': '/dev/sda'})
        self.assertIn('Flatpak sandbox', check.summary)
        self.assertNotIn('not installed', check.summary)


class MetadataTests(unittest.TestCase):
    def test_desktop_entry_matches_application_identity(self):
        p = configparser.ConfigParser(interpolation=None)
        p.read(ROOT / 'data' / (APP_ID + '.desktop'))
        entry = p['Desktop Entry']
        self.assertEqual(entry['Name'], 'Acelip Scope')
        self.assertEqual(entry['Exec'], 'acelip-scope')
        self.assertEqual(entry['Icon'], APP_ID)
        self.assertEqual(entry['Terminal'], 'false')
        self.assertIn('System;', entry['Categories'])

    def test_appstream_required_metadata(self):
        node = ET.parse(ROOT / 'data' / (APP_ID + '.metainfo.xml')).getroot()
        self.assertEqual(node.attrib['type'], 'desktop-application')
        self.assertEqual(node.findtext('id'), APP_ID)
        self.assertEqual(node.findtext('name'), 'Acelip Scope')
        for tag in ('summary', 'description/p', 'metadata_license', 'project_license', 'launchable', 'keywords/keyword'):
            self.assertTrue(node.findtext(tag), tag)
        self.assertEqual(node.find('releases/release').attrib['version'], __version__)
        self.assertEqual({u.get('type'):u.text for u in node.findall('url')},{
            'homepage':IDENTITY['homepage_url'],'vcs-browser':IDENTITY['repository_url'],
            'help':IDENTITY['support_url']})

    def test_manifest_minimum_permissions(self):
        manifest = json.loads(packaging.MANIFEST.read_text())
        self.assertEqual(manifest['app-id'], APP_ID)
        self.assertEqual(manifest['command'], 'acelip-scope')
        for arg in manifest['finish-args']:
            self.assertNotIn('--filesystem', arg)
            self.assertNotIn('--device', arg)
            self.assertNotIn('--socket=session-bus', arg)
            self.assertNotIn('--share=network', arg)
        self.assertIn('--env=GTK_USE_PORTAL=1', manifest['finish-args'])

    def test_project_icon_is_scalable(self):
        node = ET.parse(ROOT / 'data/acelip-scope-symbolic.svg').getroot()
        self.assertEqual(node.attrib['viewBox'], '0 0 128 128')

    def test_version_consistency(self):
        import tomllib
        self.assertEqual(tomllib.loads((ROOT / 'pyproject.toml').read_text())['tool']['setuptools']['dynamic']['version']['attr'], 'lucy_diagnose.__version__')


class ArtifactTests(unittest.TestCase):
    def test_flatpak_name(self):
        self.assertEqual(packaging.artifact_name('Flatpak', 'x86_64'), f'acelip-scope-{__version__}-x86_64.flatpak')

    def test_appimage_name(self):
        self.assertEqual(packaging.artifact_name('AppImage', 'aarch64'), f'acelip-scope-{__version__}-aarch64.AppImage')

    def test_name_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            packaging.artifact_name('AppImage', '../../tmp')

    def test_checksums_generate_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / 'example.AppImage').write_bytes(b'abc')
            text = packaging.checksums(d)
            self.assertEqual(text, 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  example.AppImage\n')
            self.assertEqual(packaging.checksums(d), text)

    def test_changed_artifact_rejects_stale_checksums(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / 'example.flatpak'
            p.write_bytes(b'first')
            packaging.checksums(d)
            p.write_bytes(b'second')
            with self.assertRaises(FileExistsError):
                packaging.checksums(d)

    def test_no_fake_checksums_on_empty_build(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                packaging.checksums(Path(d))

    def test_artifact_overwrite_refused_before_tools_run(self):
        with tempfile.TemporaryDirectory() as d, patch.object(packaging, 'verify_runtime') as verify:
            p = Path(d) / packaging.artifact_name('Flatpak')
            p.write_bytes(b'keep')
            with self.assertRaises(FileExistsError):
                packaging.build('Flatpak', Path(d))
            self.assertEqual(p.read_bytes(), b'keep')
            verify.assert_not_called()

    def test_staging_keeps_themes_and_excludes_bytecode(self):
        with tempfile.TemporaryDirectory() as d, patch.object(packaging, 'provenance', return_value=({'commit': 'a' * 40}, 1)):
            packaging.stage(Path(d), 'Flatpak')
            root = Path(d) / 'share/acelip-scope/lucy_diagnose'
            self.assertTrue((root / 'themes/base.css').is_file())
            self.assertTrue((root / 'themes/catalog.py').is_file())
            self.assertFalse(list(root.rglob('*.pyc')))
            self.assertEqual(json.loads((root / '_build.json').read_text())['commit'], 'a' * 40)

try:
    from gi.repository import GLib
except ImportError:
    GLib = None


@unittest.skipUnless(GLib, 'Optional GLib binding needed for bundle-format tests')
class FlatpakBundleTests(unittest.TestCase):
    def bundle(self, timestamp):
        signature = '(a{sv}tayay(a{sv}aya(say)sstayay)aya(uayttay)a(yaytt))'
        return GLib.Variant(signature, ({'ref': GLib.Variant('s', 'app/' + APP_ID + '/x86_64/devel')},
            timestamp, [], [1] * 32, ({}, [], [], 'subject', '', 42, [], []), [], [], [])).get_data_as_bytes().get_data()

    def test_generation_timestamp_does_not_change_reproduction(self):
        self.assertEqual(packaging.normalize_flatpak_bytes(self.bundle(123), 1000),
                         packaging.normalize_flatpak_bytes(self.bundle(456), 1000))

    def test_normalization_is_idempotent(self):
        data = packaging.normalize_flatpak_bytes(self.bundle(123), 1000)
        self.assertEqual(packaging.normalize_flatpak_bytes(data, 1000), data)

    def test_malformed_bundle_is_rejected(self):
        with self.assertRaises(ValueError):
            packaging.normalize_flatpak_bytes(b'invalid bundle', 1000)


class AppImageStorageTests(unittest.TestCase):
    def test_own_fuse_mount_is_not_a_full_host_disk(self):
        from lucy_diagnose.platform.linux.storage import filesystem_usage
        runner = Mock()
        runner.run.return_value = Result((), json.dumps({'filesystems': [
            {'target': '/tmp/.mount_lucy', 'fstype': 'fuse.lucy', 'use%': '100%', 'used': 10, 'size': 10, 'avail': 0},
            {'target': '/home', 'fstype': 'ext4', 'use%': '100%', 'used': 10, 'size': 10, 'avail': 0}]}), code=0)
        with patch.dict(os.environ, {'APPDIR': '/tmp/.mount_lucy'}):
            checks = filesystem_usage(runner)
        self.assertEqual(checks[0].title, 'AppImage filesystem')
        self.assertEqual(checks[0].status, Status.INFO)
        self.assertEqual(checks[1].status, Status.ERROR)

    def test_unrelated_fuse_mount_still_reports_capacity(self):
        from lucy_diagnose.platform.linux.storage import filesystem_usage
        runner = Mock()
        runner.run.return_value = Result((), json.dumps({'filesystems': [
            {'target': '/data', 'fstype': 'fuse.sshfs', 'use%': '100%', 'used': 10, 'size': 10, 'avail': 0}]}), code=0)
        with patch.dict(os.environ, {'APPDIR': '/tmp/.mount_lucy'}):
            self.assertEqual(filesystem_usage(runner)[0].status, Status.ERROR)
