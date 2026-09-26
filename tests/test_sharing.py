import json
import unittest
from unittest.mock import patch

from lucy_diagnose.platform.linux.sharing import UNITS, collect, parse_units
from lucy_diagnose.models import Status
from lucy_diagnose.runner import Result
from tests.test_collectors import FakeRunner


class SharingTests(unittest.TestCase):
    def test_service_parser_and_portal_read_has_no_activation(self):
        states = '\n\n'.join(f'Id={name}\nLoadState=loaded\nActiveState=active\nSubState=running' for name in UNITS)
        self.assertEqual(len(parse_units(states)), 5)
        runner = FakeRunner({'systemctl': Result((), states, code=0),
                             'busctl': Result((), json.dumps({'type': 'u', 'data': [3]}), code=0),
                             'ps': Result((), 'discord\npipewire', code=0), 'journalctl': Result((), '', code=0)})
        with patch('lucy_diagnose.platform.linux.sharing.shutil.which', return_value=None):
            checks = collect(runner)
        by_title = {c.title: c for c in checks}
        self.assertEqual(by_title['ScreenCast portal'].summary, 'Supports monitors, windows')
        self.assertEqual(by_title['ScreenCast portal'].status, Status.OK)
        self.assertIn('unverified', by_title['Screen-sharing verification'].summary)
        bus_call = next(call for call in runner.calls if call[0] == 'busctl')
        self.assertIn('--auto-start=no', bus_call)
        self.assertIn('--allow-interactive-authorization=no', bus_call)
        self.assertIn('get-property', bus_call)
        self.assertFalse(any('start' in call or 'restart' in call or 'CreateSession' in call for call in runner.calls))

    def test_unavailable_and_malformed_responses(self):
        with patch('lucy_diagnose.platform.linux.sharing.shutil.which', return_value=None):
            checks = collect(FakeRunner())
            self.assertTrue(any(c.status == Status.UNAVAILABLE for c in checks))
            checks = collect(FakeRunner({'busctl': Result((), '{broken', code=0)}))
            self.assertTrue(any(c.title == 'ScreenCast portal' and c.status == Status.UNAVAILABLE for c in checks))
