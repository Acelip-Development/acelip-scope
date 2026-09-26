"""Real-run regressions plus explicitly synthetic portability edge cases."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lucy_diagnose.models import DistroInfo, ServiceState, ServiceStatus, Status, Support
from lucy_diagnose.platform.linux.audio import audio_capabilities
from lucy_diagnose.platform.linux.desktop import backend_for_desktop, detect_desktop
from lucy_diagnose.platform.linux.distro import parse_os_release
from lucy_diagnose.platform.linux.health import package_health
from lucy_diagnose.platform.linux.integrity import verify_packages
from lucy_diagnose.platform.linux.packages import Packages
from lucy_diagnose.platform.linux.sensors import sensor_status
from lucy_diagnose.platform.linux.services import Services
from lucy_diagnose.platform.linux.sharing import collect
from lucy_diagnose.platform.linux.storage import device_health
from lucy_diagnose.runner import Result
from tests.test_collectors import FakeRunner
from tests.test_platform_packages_services import capabilities


class RealRunRegressions(unittest.TestCase):
    def test_gdm_alias_retains_requested_identity(self):
        text = 'Id=gdm.service\nNames=gdm.service display-manager.service\nLoadState=loaded\nActiveState=active\nSubState=running'
        runner = FakeRunner({'systemctl': Result((), text, code=0)})
        state = Services(capabilities('systemctl'), True).get('display-manager.service', runner=runner)
        self.assertEqual((state.name, state.state), ('display-manager.service', ServiceStatus.RUNNING))
        self.assertIn('Id=gdm.service', state.evidence)

    def test_multiple_alias_results_are_not_positionally_mapped(self):
        text = ('Id=b.service\nNames=b.service alias-b.service\nLoadState=loaded\nActiveState=failed\n\n'
                'Id=a.service\nNames=a.service alias-a.service\nLoadState=loaded\nActiveState=active')
        states = Services(capabilities('systemctl'), True).get_many(('alias-a.service', 'alias-b.service'),
                           runner=FakeRunner({'systemctl': Result((), text, code=0)}))
        self.assertEqual([s.state for s in states], [ServiceStatus.RUNNING, ServiceStatus.FAILED])

    def test_empty_service_query_never_queries_manager_properties(self):
        runner = FakeRunner()
        self.assertEqual(Services(capabilities('systemctl'), True).get_many([], runner=runner), [])
        self.assertFalse(runner.calls)

    def test_missing_user_bus_preserves_unknown_state(self):
        result = Result((), stderr='Failed to connect to user scope bus: No medium found', code=1)
        state = Services(capabilities('systemctl'), True).get('pipewire.service', 'user', FakeRunner({'systemctl': result}))
        self.assertEqual((state.state, state.support), (ServiceStatus.UNKNOWN, Support.UNAVAILABLE))

    def test_real_image_release_fields(self):
        fixtures = json.loads((Path(__file__).parent / 'fixtures/linux-platforms.json').read_text())
        for row in fixtures['distributions']:
            with self.subTest(row['label']):
                info = parse_os_release(row['release'])
                self.assertEqual((info.id, info.family, info.version_id), (row['id'], row['family'], row['version']))
                self.assertNotEqual(info.name, 'Unknown Linux distribution')

    def test_desktop_matrix_with_owned_backends(self):
        fixtures = json.loads((Path(__file__).parent / 'fixtures/linux-platforms.json').read_text())
        for row in fixtures['desktops']:
            with self.subTest(row['name']):
                info = detect_desktop(row['env'])
                self.assertEqual((info.environment, info.display_server), (row['name'], row['display']))
                self.assertEqual(backend_for_desktop(info.environment, row['owned']), row['backend'])

    def test_id_precedence_over_conflicting_id_like(self):
        self.assertEqual(parse_os_release('ID=opensuse-tumbleweed\nID_LIKE="debian arch"').family, 'opensuse')

    def test_fedora_real_package_absence(self):
        query = Packages(DistroInfo(family='fedora-rhel'), capabilities('rpm'))
        item = query.find('discord', FakeRunner({'rpm': Result((), 'package discord is not installed\n', code=1)}))[0]
        self.assertEqual((item.installed, item.support), (False, Support.SUPPORTED))

    def test_debian_real_package_absence_message(self):
        query = Packages(DistroInfo(family='debian'), capabilities('dpkg-query'))
        result = Result((), stderr='dpkg-query: no packages found matching discord\n', code=1)
        item = query.find('discord', FakeRunner({'dpkg-query': result}))[0]
        self.assertEqual((item.installed, item.support), (False, Support.SUPPORTED))

    def test_arch_real_package_absence(self):
        query = Packages(DistroInfo(family='arch'), capabilities('pacman'))
        item = query.find('discord', FakeRunner({'pacman': Result((), stderr="error: package 'discord' was not found", code=1)}))[0]
        self.assertEqual((item.installed, item.support), (False, Support.SUPPORTED))

    def test_rpm_database_failure_is_not_absence(self):
        query = Packages(DistroInfo(family='opensuse'), capabilities('rpm'))
        item = query.find('discord', FakeRunner({'rpm': Result((), stderr='error: cannot open Packages database', code=1)}))[0]
        self.assertIsNone(item.installed)
        self.assertEqual(item.support, Support.UNAVAILABLE)

    def test_no_hwmon_in_container_is_unavailable(self):
        with tempfile.TemporaryDirectory() as root:
            readings, support = sensor_status(FakeRunner({'sensors': Result((), problem='Command not installed: sensors')}), Path(root))
        self.assertEqual((readings, support), ([], Support.UNAVAILABLE))


class IntegrityTests(unittest.TestCase):
    def test_rpm_clean_has_scripts_and_dependencies_disabled(self):
        runner = FakeRunner({'rpm': Result((), code=0)})
        check = verify_packages(runner, 'fedora-rhel')
        self.assertEqual((check.status, check.count), (Status.OK, 0))
        self.assertEqual(runner.calls, [('rpm', '-Va', '--noscripts', '--nodeps')])

    def test_opensuse_uses_same_safe_rpm_verification(self):
        runner = FakeRunner({'rpm': Result((), 'S.5....T.  c /etc/example\n', code=1)})
        check = verify_packages(runner, 'opensuse')
        self.assertEqual((check.status, check.count), (Status.WARNING, 1))
        self.assertIn('--noscripts', runner.calls[0])

    def test_rpm_missing_files_are_differences(self):
        check = verify_packages(FakeRunner({'rpm': Result((), 'missing     /usr/bin/example\n', code=1)}), 'fedora-rhel')
        self.assertEqual((check.status, check.count), (Status.WARNING, 1))

    def test_rpm_unreadable_files_are_partial(self):
        check = verify_packages(FakeRunner({'rpm': Result((), 'SM5??????    /private\n', code=1)}), 'fedora-rhel')
        self.assertEqual(check.support, Support.PARTIAL)

    def test_rpm_db_error_never_becomes_clean_integrity(self):
        check = verify_packages(FakeRunner({'rpm': Result((), stderr='error: cannot open database', code=1)}), 'fedora-rhel')
        self.assertEqual(check.status, Status.UNAVAILABLE)

    def test_rpm_unknown_output_is_unavailable(self):
        check = verify_packages(FakeRunner({'rpm': Result((), 'unexpected format', code=0)}), 'opensuse')
        self.assertEqual(check.status, Status.UNAVAILABLE)

    def test_timeout_retains_partial_evidence(self):
        check = verify_packages(FakeRunner({'rpm': Result((), '.M.......    /usr\n', problem='Timed out after 20 seconds')}), 'fedora-rhel')
        self.assertEqual(check.support, Support.PARTIAL)
        self.assertIn('/usr', check.details)

    def test_missing_integrity_tool_is_unavailable(self):
        check = verify_packages(FakeRunner({'pacman': Result((), problem='Command not installed: pacman')}), 'arch')
        self.assertEqual(check.support, Support.UNAVAILABLE)
        self.assertEqual(check.summary, 'Command not installed')

    def test_pacman_sums_actual_altered_counts(self):
        runner = FakeRunner({'pacman': Result((), 'acl: 103 total files, 17 altered files\nbash: 270 total files, 20 altered files\n',
                                             stderr='warning: acl: /usr (Permissions mismatch)', code=1)})
        check = verify_packages(runner, 'arch')
        self.assertEqual((check.status, check.count, check.support), (Status.WARNING, 37, Support.PARTIAL))
        self.assertEqual(runner.calls, [('pacman', '-Qkk')])

    def test_pacman_clean_is_metadata_only(self):
        check = verify_packages(FakeRunner({'pacman': Result((), 'bash: 270 total files, 0 altered files\n', code=0)}), 'arch')
        self.assertEqual(check.support, Support.PARTIAL)
        self.assertIn('not a content-digest audit', check.details)

    def test_pacman_missing_mtree_never_claims_clean(self):
        check = verify_packages(FakeRunner({'pacman': Result((), stderr='warning: bash: no mtree file', code=1)}), 'arch')
        self.assertEqual(check.status, Status.UNAVAILABLE)

    def test_quick_scan_omits_full_file_verification(self):
        runner = FakeRunner()
        for family in ('fedora-rhel', 'opensuse', 'arch'):
            self.assertEqual(package_health(runner, DistroInfo(family=family))[0].support, Support.PARTIAL)
        self.assertFalse(runner.calls)

    def test_unknown_integrity_family_does_not_guess_commands(self):
        runner = FakeRunner()
        self.assertEqual(verify_packages(runner, 'unknown').support, Support.UNSUPPORTED)
        self.assertFalse(runner.calls)


class AudioSmartTests(unittest.TestCase):
    states = [ServiceState(name, ServiceStatus.RUNNING) for name in ('pipewire.service', 'pipewire-pulse.service')]

    def audio(self, commands, responses=None, states=None):
        runner = FakeRunner(responses)
        check = audio_capabilities(runner, Services(), self.states if states is None else states,
                                   capabilities(*commands), runtime='/run/user/1000')
        return check, runner

    def test_pactl_without_wpctl_is_supported(self):
        check, runner = self.audio(('pactl',), {'pactl': Result((), 'Server Name: PulseAudio (on PipeWire 1.4)\n', code=0)})
        self.assertEqual(check.support, Support.SUPPORTED)
        self.assertIn('pactl', check.summary)
        self.assertFalse(any(call[0] == 'wpctl' for call in runner.calls))

    def test_wpctl_without_pactl_is_supported(self):
        check, _ = self.audio(('wpctl',), {'wpctl': Result((), 'PipeWire 1.4\nAudio\n Sinks:\n', code=0)})
        self.assertEqual(check.support, Support.SUPPORTED)

    def test_audio_service_without_optional_clients_is_partial(self):
        check, _ = self.audio(())
        self.assertEqual((check.support, check.status), (Support.PARTIAL, Status.INFO))

    def test_dormant_audio_never_connects_to_clients(self):
        check, runner = self.audio(('wpctl', 'pactl'), states=[])
        self.assertEqual(check.support, Support.UNAVAILABLE)
        self.assertFalse(any(call[0] in {'wpctl', 'pactl'} for call in runner.calls))

    def test_audio_process_only_does_not_require_systemd(self):
        check, _ = self.audio((), {'ps': Result((), 'pipewire\n', code=0)}, states=[])
        self.assertEqual(check.support, Support.PARTIAL)

    def test_malformed_audio_client_is_not_supported(self):
        check, _ = self.audio(('wpctl',), {'wpctl': Result((), 'unrelated output', code=0)})
        self.assertEqual(check.support, Support.PARTIAL)

    def test_pulse_client_uses_explicit_local_server(self):
        _, runner = self.audio(('pactl',))
        self.assertIn(('pactl', '--server=unix:/run/user/1000/pulse/native', 'info'), runner.calls)

    def test_negative_portal_mask_is_not_capture_support(self):
        with patch('lucy_diagnose.platform.linux.sharing.package_checks', return_value=[]):
            checks = collect(FakeRunner({'busctl': Result((), '{"data":[-1]}', code=0)}),
                             services=Services(capabilities(), False), desktop=detect_desktop({}))
        self.assertEqual(next(c for c in checks if c.title == 'ScreenCast portal').status, Status.UNAVAILABLE)

    def test_smart_missing_tool_is_distinct(self):
        check = device_health(FakeRunner({'smartctl': Result((), problem='Command not installed: smartctl')}), {'path': '/dev/sda'})
        self.assertEqual((check.summary, check.support), ('Command not installed', Support.UNAVAILABLE))

    def test_smart_unsupported_bridge_is_distinct(self):
        check = device_health(FakeRunner({'smartctl': Result((), '{"smartctl":{"messages":[{"string":"Unknown USB bridge"}]}}', code=2)}), {'path': '/dev/sda'})
        self.assertEqual(check.support, Support.UNSUPPORTED)

    def test_smart_explicit_unsupported_device(self):
        check = device_health(FakeRunner({'smartctl': Result((), '{"smart_support":{"available":false}}', code=0)}), {'path': '/dev/sda'})
        self.assertEqual((check.status, check.support), (Status.UNAVAILABLE, Support.UNSUPPORTED))

    def test_smart_success_is_separate_from_permissions(self):
        check = device_health(FakeRunner({'smartctl': Result((), '{"smart_status":{"passed":true}}', code=0)}), {'path': '/dev/sda'})
        self.assertEqual((check.status, check.support), (Status.OK, Support.SUPPORTED))


class DegradationTests(unittest.TestCase):
    def test_full_scan_without_optional_commands_has_no_errors(self):
        from lucy_diagnose.scanner import scan
        class MissingRunner(FakeRunner):
            def run(self, *args, timeout=7):
                self.calls.append(args)
                return Result(args, problem='Command not installed: ' + args[0])
        runner = MissingRunner()
        with patch('shutil.which', return_value=None), \
             patch('lucy_diagnose.platform.linux.sensors.read_hwmon', return_value=[]), \
             patch('lucy_diagnose.platform.linux.ai_stack.ollama_get', side_effect=OSError('No endpoint')):
            snapshot = scan('Full Scan', runner)
        checks = [c for items in snapshot.sections.values() for c in items]
        self.assertFalse(any(c.status == Status.ERROR for c in checks))
        self.assertFalse(any(c.summary.startswith('Collector failed') for c in checks))
        for name in ('smartctl', 'sensors', 'wpctl', 'pactl', 'nmcli', 'lspci', 'journalctl', 'systemctl', 'flatpak', 'snap'):
            self.assertEqual(capabilities().find_command(name).support, Support.UNAVAILABLE)

    def test_broken_gtk_shared_library_has_actionable_launch_error(self):
        import builtins
        import contextlib
        import io
        from lucy_diagnose.__main__ import main
        original = builtins.__import__
        def import_module(name, *args, **kwargs):
            if name == 'ui.application':
                raise AssertionError('missing GTK shared library')
            return original(name, *args, **kwargs)
        output = io.StringIO()
        with patch('sys.argv', ['lucy-diagnose']), patch('builtins.__import__', side_effect=import_module), \
             patch('lucy_diagnose.__main__.configure_logging'), \
             patch('lucy_diagnose.platform.linux.backend.LinuxPlatform.configure_ui_environment'), \
             contextlib.redirect_stderr(output):
            self.assertEqual(main(), 1)
        self.assertIn('GTK runtime unavailable', output.getvalue())
        self.assertNotIn('Traceback', output.getvalue())
