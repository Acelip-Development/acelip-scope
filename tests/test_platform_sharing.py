import json
import unittest
from unittest.mock import patch

from lucy_diagnose.models import Support, Status
from lucy_diagnose.platform.linux.desktop import detect_desktop
from lucy_diagnose.platform.linux.services import Services
from lucy_diagnose.platform.linux.sharing import collect
from lucy_diagnose.runner import Result
from tests.test_collectors import FakeRunner
from tests.test_platform_packages_services import capabilities


class SharingPlatformTests(unittest.TestCase):
    def collect(self, desktop, responses=None, systemd=True):
        runner = FakeRunner(responses or {})
        services = Services(capabilities('systemctl'), systemd)
        with patch('lucy_diagnose.platform.linux.sharing.package_checks', return_value=[]):
            checks = collect(runner, services=services, desktop=detect_desktop(desktop))
        return checks, runner

    def test_kde_does_not_query_or_require_gnome_service(self):
        checks, runner = self.collect({'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'})
        self.assertFalse(any('gnome' in arg.lower() for call in runner.calls for arg in call))
        self.assertFalse(any('gnome' in c.title.lower() for c in checks))
        self.assertTrue(any('kde' in arg for call in runner.calls for arg in call))

    def test_unknown_desktop_backend_is_partial(self):
        checks, _ = self.collect({})
        backend = next(c for c in checks if c.title == 'Desktop portal backend')
        self.assertEqual(backend.support, Support.PARTIAL)
        self.assertNotEqual(backend.status, Status.ERROR)

    def test_missing_pipewire_is_not_error(self):
        checks, _ = self.collect({'XDG_CURRENT_DESKTOP': 'GNOME'}, {'systemctl': Result((), 'Id=pipewire.service\nLoadState=not-found', code=0)})
        check = next(c for c in checks if c.title == 'pipewire.service')
        self.assertEqual(check.summary, 'NOT_FOUND')
        self.assertNotEqual(check.status, Status.ERROR)

    def test_missing_wireplumber_tries_alternative_session_manager(self):
        checks, runner = self.collect({'XDG_CURRENT_DESKTOP': 'GNOME'}, {'systemctl': Result((), 'Id=wireplumber.service\nLoadState=not-found', code=0)})
        self.assertTrue(any('pipewire-media-session.service' in call for call in runner.calls))
        self.assertNotEqual(next(c for c in checks if c.title == 'wireplumber.service').status, Status.ERROR)

    def test_no_systemd_explicit_unsupported(self):
        checks, runner = self.collect({'XDG_CURRENT_DESKTOP': 'XFCE'}, systemd=False)
        self.assertEqual(next(c for c in checks if c.title == 'pipewire.service').support, Support.UNSUPPORTED)
        self.assertFalse(any(call[0] == 'systemctl' for call in runner.calls))

    def test_x11_does_not_claim_wayland_mismatch(self):
        checks, _ = self.collect({'XDG_SESSION_TYPE': 'x11'}, {'busctl': Result((), json.dumps({'data': [0]}), code=0)})
        self.assertFalse(any(c.title == 'Wayland capture prerequisites' for c in checks))

    def test_scan_does_not_open_capture_or_mutate_services(self):
        _, runner = self.collect({'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'})
        forbidden = {'CreateSession', 'SelectSources', 'Start', 'OpenPipeWireRemote', 'start', 'restart', 'enable', 'disable', 'sudo', 'pkexec'}
        self.assertFalse(any(forbidden.intersection(call) for call in runner.calls))
