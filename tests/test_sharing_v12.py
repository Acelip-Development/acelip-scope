from pathlib import Path
import stat
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from lucy_diagnose.platform.linux.sharing import collect, package_checks, pipewire_socket, portal_backends
from lucy_diagnose.models import Status, DistroInfo
from lucy_diagnose.platform.linux.packages import Packages
from lucy_diagnose.runner import Result
from lucy_diagnose.sharing_test import SharingTest
from tests.test_collectors import FakeRunner


class SharingV12Tests(unittest.TestCase):
    def test_package_sources_without_starting_discord(self):
        runner = FakeRunner({'dpkg-query': Result((), 'ii \t1.2.3\n', code=0),
                             'snap': Result((), 'discord 0.0.1', code=0),
                             'flatpak': Result((), 'com.discordapp.Discord\t0.0.2\tuser', code=0)})
        with patch('lucy_diagnose.platform.linux.sharing.shutil.which', return_value='/usr/bin/tool'):
            checks = package_checks(runner, Packages(DistroInfo(family='debian')))
        source = next(c for c in checks if c.title == 'Discord installation source')
        self.assertEqual(source.summary, 'deb, Snap, Flatpak')
        self.assertTrue(any('--show-permissions' in call for call in runner.calls))
        self.assertTrue(any('connections' in call for call in runner.calls))
        self.assertFalse(any(call[0] == 'discord' for call in runner.calls))

    def test_missing_package_tools_and_permission_denial(self):
        with patch('lucy_diagnose.platform.linux.sharing.shutil.which', return_value=None):
            self.assertEqual(sum(c.status == Status.UNAVAILABLE for c in package_checks(FakeRunner())), 3)
        with patch('lucy_diagnose.platform.linux.sharing.shutil.which', return_value='/usr/bin/tool'):
            checks = package_checks(FakeRunner({'snap': Result((), stderr='Permission denied', code=1)}))
            self.assertEqual(next(c for c in checks if c.title == 'Discord Snap').status, Status.UNAVAILABLE)

    def test_removed_deb_is_not_installed(self):
        with patch('lucy_diagnose.platform.linux.sharing.shutil.which', return_value='/usr/bin/tool'):
            checks = package_checks(FakeRunner({'dpkg-query': Result((), 'rc \t1.0', code=0)}), Packages(DistroInfo(family='debian')))
        self.assertIn('Not installed', next(c for c in checks if c.title == 'Discord deb').summary)

    def test_portal_metadata_and_missing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(portal_backends(root).status, Status.UNAVAILABLE)
            (root / 'gnome.portal').write_text('[portal]\nInterfaces=org.freedesktop.impl.portal.ScreenCast;\nUseIn=gnome\n')
            self.assertIn('ScreenCast=True', portal_backends(root).details)
            (root / 'bad.portal').write_text('malformed')
            self.assertEqual(portal_backends(root).status, Status.UNAVAILABLE)

    def test_pipewire_socket_check_does_not_connect(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(pipewire_socket(directory).status, Status.UNAVAILABLE)
            path = Path(directory) / 'pipewire-0'
            path.write_text('not a socket')
            self.assertEqual(pipewire_socket(directory).status, Status.WARNING)
            with patch.object(Path, 'stat', return_value=SimpleNamespace(st_mode=stat.S_IFSOCK | 0o600)):
                self.assertIn('not connected', pipewire_socket(directory).summary)

    def test_wayland_zero_sources_mismatch(self):
        runner = FakeRunner({'busctl': Result((), '{"data":[0]}', code=0)})
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'wayland'}), patch('lucy_diagnose.platform.linux.sharing.shutil.which', return_value=None):
            checks = collect(runner)
        self.assertTrue(any(c.title == 'Wayland capture prerequisites' and c.status == Status.WARNING for c in checks))
        self.assertFalse(any(any(a in call for a in ('CreateSession', 'SelectSources', 'Start', 'OpenPipeWireRemote', 'sudo', 'restart')) for call in runner.calls))

    def test_manual_test_requires_fresh_consent_and_receiver_confirmation(self):
        test = SharingTest()
        self.assertFalse(test.active)
        self.assertIsNone(test.result)
        with self.assertRaises(ValueError):
            test.begin()
        test.begin(True)
        with self.assertRaises(ValueError):
            test.finish('PASS')
        result = test.finish('PASS', True)
        self.assertIn('user reported', result.summary)
        self.assertIn('did not capture', result.details)
        with self.assertRaises(ValueError):
            test.finish('PASS', True)
        with self.assertRaises(ValueError):
            test.begin()

    def test_manual_test_cancel_is_inconclusive(self):
        test = SharingTest()
        self.assertIsNone(test.cancel())
        test.begin(True)
        self.assertIn('INCONCLUSIVE', test.cancel().summary)
        self.assertFalse(test.active)
        self.assertIsNone(test.cancel())

    def test_manual_failure_is_user_reported_warning(self):
        test = SharingTest()
        test.begin(True)
        result = test.finish('FAIL')
        self.assertEqual(result.status, Status.WARNING)
        self.assertEqual(result.source, 'Explicit manual test / user report')
