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
        return self.responses.get(args[0], Result(args, problem='Permission denied'))


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
