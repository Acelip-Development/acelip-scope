from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lucy_diagnose.models import Support
from lucy_diagnose.platform.base import Platform, UnsupportedPlatform
from lucy_diagnose.platform.detect import get_platform
from lucy_diagnose.platform.linux.distro import detect_distro, parse_os_release
from lucy_diagnose.platform.linux.desktop import detect_desktop, backend_for_desktop, owned_portal_backends
from lucy_diagnose.scanner import MODES, scan
from lucy_diagnose.analysis import prepare_analysis
from lucy_diagnose.runner import Result
from tests.test_collectors import FakeRunner


class PlatformDetectionTests(unittest.TestCase):
    def test_factory_linux_and_protocol(self):
        platform = get_platform('Linux')
        self.assertEqual(platform.name, 'Linux')
        self.assertIsInstance(platform, Platform)

    def test_factory_windows_placeholder(self):
        platform = get_platform('Windows')
        self.assertEqual(platform.name, 'Windows')
        self.assertIsInstance(platform, Platform)
        self.assertEqual(platform.get_desktop_info().support, Support.UNSUPPORTED)

    def test_factory_macos_placeholder(self):
        self.assertEqual(get_platform('Darwin').name, 'macOS')
        self.assertEqual(get_platform('macOS').name, 'macOS')

    def test_factory_unknown(self):
        self.assertIsInstance(get_platform('Unrecognized'), UnsupportedPlatform)

    def test_native_factory_selection(self):
        with patch('lucy_diagnose.platform.detect.platform.system', return_value='Windows'):
            self.assertEqual(get_platform().name, 'Windows')

    def test_unsupported_modes_never_execute_diagnostics(self):
        with patch('subprocess.Popen', side_effect=AssertionError('No execution allowed')):
            for name in ('Windows', 'Darwin', 'Unknown'):
                platform = get_platform(name)
                for mode in MODES:
                    snapshot = scan(mode, platform=platform)
                    self.assertTrue(snapshot.sections)
                    self.assertTrue(all(c.support == Support.UNSUPPORTED for checks in snapshot.sections.values() for c in checks))
                self.assertTrue(all(v is None for v in platform.create_sampler().sample(platform.create_runner()).values.values()))
                self.assertEqual(platform.packages.find('discord')[0].support, Support.UNSUPPORTED)
                self.assertEqual(platform.capabilities.find_command('sensors').support, Support.UNSUPPORTED)

    def test_unsupported_ai_preview_does_not_offer_posix_command(self):
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED'):
            prepare_analysis('Codex', 'data', platform=get_platform('Windows'))

    def test_debian_family(self):
        for identifier in ('debian', 'ubuntu', 'linuxmint', 'pop', 'pop_os'):
            self.assertEqual(parse_os_release(f'ID={identifier}').family, 'debian')
        self.assertEqual(parse_os_release('ID=custom\nID_LIKE="ubuntu debian"').family, 'debian')

    def test_fedora_rhel_family(self):
        for identifier in ('fedora', 'rhel', 'rocky', 'almalinux', 'centos', 'centos-stream'):
            self.assertEqual(parse_os_release(f'ID={identifier}').family, 'fedora-rhel')
        self.assertEqual(parse_os_release('ID=custom\nID_LIKE="rhel fedora"').family, 'fedora-rhel')

    def test_arch_family(self):
        for identifier in ('arch', 'endeavouros', 'manjaro', 'garuda'):
            self.assertEqual(parse_os_release(f'ID={identifier}').family, 'arch')
        self.assertEqual(parse_os_release('ID=custom\nID_LIKE=arch').family, 'arch')

    def test_opensuse_family(self):
        for identifier in ('opensuse-leap', 'opensuse-tumbleweed', 'opensuse'):
            self.assertEqual(parse_os_release(f'ID={identifier}').family, 'opensuse')

    def test_unknown_malformed_and_shell_text_are_data(self):
        info = parse_os_release('ID=unknown\nNAME="Unclosed\nBROKEN\nPRETTY_NAME="$(touch forbidden)"')
        self.assertEqual(info.family, 'unknown')
        self.assertEqual(info.name, '$(touch forbidden)')

    def test_distro_fields_and_file_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'release'
            path.write_text('ID=ubuntu\nPRETTY_NAME="Ubuntu sample"\nVERSION="26.04 LTS"\nVERSION_ID="26.04"\nID_LIKE=debian')
            info = detect_distro((path.with_name('missing'), path))
            self.assertEqual((info.name, info.version_id, info.id_like), ('Ubuntu sample', '26.04', ('debian',)))
            self.assertEqual(detect_distro((path.with_name('missing'),)).family, 'unknown')

    def test_gnome_wayland(self):
        info = detect_desktop({'XDG_CURRENT_DESKTOP': 'ubuntu:GNOME', 'XDG_SESSION_TYPE': 'wayland', 'DESKTOP_SESSION': 'ubuntu'})
        self.assertEqual((info.environment, info.display_server, info.session_name), ('GNOME', 'Wayland', 'ubuntu'))

    def test_kde_x11(self):
        info = detect_desktop({'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'x11'})
        self.assertEqual((info.environment, info.display_server), ('KDE Plasma', 'X11'))

    def test_other_desktops(self):
        for value, expected in (('X-Cinnamon', 'Cinnamon'), ('XFCE', 'XFCE'), ('MATE', 'MATE'), ('LXQt', 'LXQt')):
            self.assertEqual(detect_desktop({'XDG_CURRENT_DESKTOP': value}).environment, expected)

    def test_session_fallback_and_unknown(self):
        self.assertEqual(detect_desktop({'WAYLAND_DISPLAY': 'wayland-0'}).display_server, 'Wayland')
        self.assertEqual(detect_desktop({'DISPLAY': ':0'}).display_server, 'X11')
        self.assertEqual(detect_desktop({'XDG_SESSION_TYPE': 'tty', 'DISPLAY': ':0'}).display_server, 'unknown')
        self.assertEqual(detect_desktop({}).environment, 'unknown')
        self.assertEqual(detect_desktop({'DESKTOP_SESSION': 'plasma-wayland'}).environment, 'KDE Plasma')

    def test_portal_backend_requires_evidence(self):
        self.assertEqual(backend_for_desktop('GNOME', ()), 'unknown')
        self.assertEqual(backend_for_desktop('KDE Plasma', ('gtk', 'kde')), 'kde')
        runner = FakeRunner({'busctl': Result((), 'org.freedesktop.impl.portal.desktop.gnome 100 portal user\n', code=0)})
        self.assertEqual(owned_portal_backends(runner), ('gnome',))
