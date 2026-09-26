import unittest
from lucy_diagnose.models import DistroInfo, ServiceStatus, Support
from lucy_diagnose.platform.linux.capabilities import Capabilities
from lucy_diagnose.platform.linux.packages import Packages
from lucy_diagnose.platform.linux.services import Services, normalize_service, service_check
from lucy_diagnose.platform.linux.health import collect
from lucy_diagnose.runner import Result
from tests.test_collectors import FakeRunner


def capabilities(*names):
    return Capabilities(lambda name: '/usr/bin/' + name if name in names else None)


class PackageServiceTests(unittest.TestCase):
    def package(self, family, command, stdout, code=0):
        query = Packages(DistroInfo(family=family), capabilities(command))
        items = query.find('discord', FakeRunner({command: Result((), stdout, code=code)}))
        return next(item for item in items if item.package_manager not in {'flatpak', 'snap'})

    def test_dpkg_normalization(self):
        package = self.package('debian', 'dpkg-query', 'ii \t1.0.159\n')
        self.assertEqual((package.version, package.source, package.package_manager), ('1.0.159', 'deb', 'dpkg'))
        self.assertTrue(package.installed)
        self.assertFalse(package.sandboxed)

    def test_rpm_normalization(self):
        package = self.package('fedora-rhel', 'rpm', 'discord\t1.0-2.fc44\n')
        self.assertEqual((package.source, package.package_manager, package.version), ('rpm', 'rpm/dnf', '1.0-2.fc44'))

    def test_zypper_uses_rpm_database(self):
        package = self.package('opensuse', 'rpm', 'discord\t1.0-2\n')
        self.assertEqual(package.package_manager, 'rpm/zypper')

    def test_pacman_normalization(self):
        self.assertEqual(self.package('arch', 'pacman', 'discord 1.0-1\n').version, '1.0-1')

    def test_flatpak_and_snap(self):
        query = Packages(DistroInfo(family='unknown'), capabilities('flatpak', 'snap'))
        items = query.find('discord', FakeRunner({'snap': Result((), 'Name Version Rev\ndiscord 1.0 123', code=0), 'flatpak': Result((), 'com.discordapp.Discord\t2.0\tuser', code=0)}))
        self.assertEqual([(p.source, p.version) for p in items if p.installed], [('Snap', '1.0'), ('Flatpak', '2.0')])
        self.assertTrue(all(p.sandboxed for p in items))

    def test_empty_flatpak_list_means_absent(self):
        query = Packages(DistroInfo(), capabilities('flatpak'))
        item = next(p for p in query.find('discord', FakeRunner({'flatpak': Result((), '', code=0)})) if p.source == 'Flatpak')
        self.assertFalse(item.installed)
        self.assertEqual(item.support, Support.SUPPORTED)

    def test_flatpak_unversioned_install_is_still_detected(self):
        query = Packages(DistroInfo(), capabilities('flatpak'))
        runner = FakeRunner({'flatpak': Result((), 'com.discordapp.Discord\t\tuser\norg.other.App\t1.0\tsystem', code=0)})
        item = next(p for p in query.find('discord', runner) if p.source == 'Flatpak')
        self.assertTrue(item.installed)
        self.assertEqual(item.support, Support.PARTIAL)
        self.assertNotIn('org.other.App', item.evidence)
        self.assertIn('--columns=application,version,installation', runner.calls[0])

    def test_missing_package_is_not_error_or_missing_tool(self):
        package = self.package('debian', 'dpkg-query', '', code=1)
        self.assertFalse(package.installed)
        self.assertEqual(package.support, Support.SUPPORTED)

    def test_missing_package_manager_is_unavailable(self):
        item = Packages(DistroInfo(family='debian'), capabilities()).find('discord', FakeRunner())[0]
        self.assertIsNone(item.installed)
        self.assertEqual(item.support, Support.UNAVAILABLE)

    def test_malformed_package_output_remains_unknown(self):
        package = self.package('arch', 'pacman', 'malformed')
        self.assertIsNone(package.installed)
        self.assertEqual(package.support, Support.UNKNOWN)

    def test_package_daemon_failure_is_not_reported_as_absence(self):
        query = Packages(DistroInfo(), capabilities('snap'))
        item = query.find('discord', FakeRunner({'snap': Result((), stderr='cannot communicate with server', code=1)}))[0]
        self.assertIsNone(item.installed)
        self.assertEqual(item.support, Support.UNAVAILABLE)

    def test_appimage_and_manual_have_low_confidence(self):
        for path, source in (('/apps/Discord.AppImage', 'AppImage'), ('/opt/custom/discord', 'manual/unknown')):
            query = Packages(DistroInfo(), Capabilities(lambda name: path if name == 'discord' else None))
            item = next(p for p in query.find('discord', FakeRunner()) if p.installed)
            self.assertEqual((item.source, item.confidence, item.install_path), (source, 'low', path))
            self.assertIsNone(item.sandboxed)

    def test_invalid_package_name_rejected_without_command(self):
        runner = FakeRunner()
        with self.assertRaises(ValueError):
            Packages().find('--install', runner)
        self.assertFalse(runner.calls)

    def test_capability_missing_and_metadata(self):
        self.assertEqual(capabilities().find_command('smartctl').support, Support.UNAVAILABLE)
        found = capabilities('smartctl').find_command('smartctl')
        self.assertEqual(found.path, '/usr/bin/smartctl')
        self.assertTrue(found.available)
        self.assertIsNone(found.version)

    def test_capability_version_only_on_opt_in(self):
        runner = FakeRunner({'/usr/bin/smartctl': Result((), 'smartctl 7.5\nMore text', code=0)})
        detector = capabilities('smartctl')
        detector.find_command('smartctl', runner)
        self.assertFalse(runner.calls)
        self.assertEqual(detector.find_command('smartctl', runner, version=True).version, 'smartctl 7.5')

    def test_systemd_system_service(self):
        runner = FakeRunner({'systemctl': Result((), 'Id=example.service\nLoadState=loaded\nActiveState=active\nSubState=running', code=0)})
        state = Services(capabilities('systemctl'), True).get('example.service', runner=runner)
        self.assertEqual((state.state, state.scope), (ServiceStatus.RUNNING, 'system'))
        self.assertNotIn('--user', runner.calls[0])

    def test_systemd_user_service(self):
        runner = FakeRunner({'systemctl': Result((), 'Id=example.service\nLoadState=loaded\nActiveState=failed\nSubState=failed', code=0)})
        state = Services(capabilities('systemctl'), True).get('example.service', 'user', runner)
        self.assertEqual((state.state, state.scope), (ServiceStatus.FAILED, 'user'))
        self.assertIn('--user', runner.calls[0])

    def test_missing_stopped_inactive_unknown_service(self):
        for data, expected in (({'LoadState': 'not-found'}, ServiceStatus.NOT_FOUND),
                               ({'ActiveState': 'inactive', 'SubState': 'dead'}, ServiceStatus.STOPPED),
                               ({'ActiveState': 'inactive', 'SubState': 'waiting'}, ServiceStatus.INACTIVE), ({}, ServiceStatus.UNKNOWN)):
            self.assertEqual(normalize_service('x', data).state, expected)

    def test_no_systemd_never_calls_service_commands(self):
        runner = FakeRunner()
        services = Services(capabilities('systemctl'), False)
        state = services.get('example.service', runner=runner)
        self.assertEqual(state.state, ServiceStatus.UNSUPPORTED)
        self.assertFalse(runner.calls)
        self.assertEqual(service_check(state).support, Support.UNSUPPORTED)

    def test_systemctl_missing_is_unsupported(self):
        self.assertEqual(Services(capabilities(), True).get('x').state, ServiceStatus.UNSUPPORTED)

    def test_service_permission_failure_is_unavailable(self):
        state = Services(capabilities('systemctl'), True).get('x', runner=FakeRunner())
        self.assertEqual(state.support, Support.UNAVAILABLE)
        self.assertNotEqual(state.state, ServiceStatus.FAILED)

    def test_process_only_is_not_service_health(self):
        state = Services().process('ollama', FakeRunner({'ps': Result((), 'ollama\nother\n', code=0)}))
        self.assertEqual((state.state, state.scope, state.support), (ServiceStatus.RUNNING, 'process', Support.PARTIAL))

    def test_non_systemd_non_debian_health_degrades(self):
        runner = FakeRunner()
        checks = collect(runner, services=Services(capabilities(), False), distro=DistroInfo(family='arch'))
        self.assertTrue(any(c.support == Support.UNSUPPORTED for c in checks))
        self.assertFalse({'systemctl', 'journalctl', 'dpkg', 'apt-mark'} & {call[0] for call in runner.calls})
