import json
import threading
import unittest
from unittest.mock import patch

from lucy_diagnose.collectors import ai_stack, health, network, overview, storage
from lucy_diagnose.models import Status
from lucy_diagnose.runner import Result
from lucy_diagnose.scanner import scan


class FakeRunner:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.cancel = threading.Event()
        self.calls = []

    def run(self, *args, timeout=7):
        self.calls.append(args)
        return self.responses.get(args, self.responses.get(args[0], Result(args, problem='Permission denied')))


class CollectorTests(unittest.TestCase):
    def test_missing_and_permissions_do_not_crash(self):
        for collector in (overview.collect, health.collect, storage.collect, network.collect):
            checks = collector(FakeRunner())
            self.assertTrue(checks)
            self.assertTrue(any(c.status == Status.UNAVAILABLE for c in checks))
        with patch('lucy_diagnose.collectors.ai_stack.shutil.which', return_value=None):
            checks = ai_stack.collect(FakeRunner(), get=lambda _: (_ for _ in ()).throw(OSError('Unavailable')))
            self.assertTrue(any(c.title == 'Ollama API' and c.status == Status.UNAVAILABLE for c in checks))

    def test_smart_exit_bitmask_reports_failure(self):
        fake = FakeRunner({'smartctl': Result(('smartctl',), json.dumps({'smart_status': {'passed': False}}), code=8)})
        self.assertEqual(storage.device_health(fake, {'path': '/dev/nvme0n1'}).status, Status.ERROR)
        fake.responses['smartctl'] = Result(('smartctl',), '{"smart_status":{"passed":true}}', code=64)
        self.assertEqual(storage.device_health(fake, {'path': '/dev/sda'}).status, Status.WARNING)
        fake.responses['smartctl'] = Result(('smartctl',), stderr='Permission denied', code=2)
        self.assertEqual(storage.device_health(fake, {'path': '/dev/sda'}).status, Status.UNAVAILABLE)

    def test_malformed_gpu_and_filesystem_data(self):
        self.assertEqual(overview.collect_gpu(FakeRunner({'nvidia-smi': Result((), 'bad', code=0)}))[0].status, Status.UNAVAILABLE)
        self.assertEqual(storage.filesystem_usage(FakeRunner({'findmnt': Result((), '{bad', code=0)}))[0].status, Status.UNAVAILABLE)

    def test_gpu_unknown_sensor_keeps_other_telemetry(self):
        responses = {
            'nvidia-smi': Result((), 'NVIDIA RTX 4070 Ti, 595.91.07, [Unknown Error], 2, 128, 12288, 22, [N/A]', code=0),
            ('nvidia-smi',): Result((), 'CUDA Version: 13.2', code=0),
        }
        checks = overview.collect_gpu(FakeRunner(responses))
        by_title = {c.title: c for c in checks}
        self.assertEqual(by_title['GPU'].status, Status.OK)
        self.assertEqual(by_title['GPU temperature'].status, Status.UNAVAILABLE)
        self.assertEqual(by_title['GPU fan speed'].status, Status.UNAVAILABLE)
        self.assertEqual(by_title['CUDA compatibility'].summary, '13.2')

    def test_network_healthy_structured_data(self):
        def result(value):
            return Result((), json.dumps(value), code=0)
        runner = FakeRunner({
            ('ip', '-j', '-details', 'address', 'show'): result([
                {'ifname': 'eth0', 'operstate': 'UP', 'addr_info': [{'local': '192.168.1.2', 'prefixlen': 24, 'family': 'inet'}]},
                {'ifname': 'wg0', 'linkinfo': {'info_kind': 'wireguard'}, 'addr_info': []}]),
            ('ip', '-j', '-4', 'route', 'show', 'default'): result([{'gateway': '192.168.1.1', 'dev': 'eth0'}]),
            ('ip', '-j', '-6', 'route', 'show', 'default'): result([]),
            'resolvectl': Result((), 'DNS Servers: 192.168.1.1', code=0),
            'ss': Result((), 'tcp LISTEN 0 128 127.0.0.1:11434 0.0.0.0:*', code=0),
            'ping': Result((), '1 received', code=0),
        })
        checks = network.collect(runner)
        by_title = {c.title: c for c in checks}
        self.assertEqual(by_title['Internet reachability'].status, Status.OK)
        self.assertEqual(by_title['VPN interfaces'].summary, 'wg0')
        self.assertIn(('ping', '-n', '-c', '1', '-W', '2', '-I', 'eth0', '192.168.1.1'), runner.calls)

    def test_mount_capacity_threshold_and_missing_values(self):
        data = {'filesystems': [{'target': '/', 'source': '/dev/root', 'fstype': 'ext4',
                                'size': 1000, 'used': 950, 'avail': 50, 'use%': '95%',
                                'children': [{'target': '/other', 'use%': None}]}]}
        checks = storage.filesystem_usage(FakeRunner({'findmnt': Result((), json.dumps(data), code=0)}))
        self.assertEqual([c.status for c in checks], [Status.ERROR, Status.UNAVAILABLE])

    def test_smart_permission_reason_is_readable(self):
        data = {'smartctl': {'messages': [{'string': 'open device: Permission denied'}]}}
        fake = FakeRunner({'smartctl': Result((), json.dumps(data), code=2)})
        check = storage.device_health(fake, {'path': '/dev/sda'})
        self.assertIn('Permission denied', check.summary)
        self.assertIn('No elevation', check.details)

    def test_scanner_contains_collector_failure(self):
        with patch('lucy_diagnose.scanner.overview.collect_gpu', side_effect=RuntimeError('test')):
            result = scan('GPU', FakeRunner())
        self.assertEqual(result.sections['Overview'][0].status, Status.UNAVAILABLE)

    def test_quick_scan_does_not_do_heavy_or_external_checks(self):
        runner = FakeRunner()
        scan('Quick Scan', runner)
        self.assertFalse({'smartctl', 'ping', 'codex', 'claude'} & {c[0] for c in runner.calls})

    def test_ollama_only_read_endpoints(self):
        with self.assertRaises(ValueError):
            ai_stack.ollama_get('/api/generate')
