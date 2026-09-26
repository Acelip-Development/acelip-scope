import sys
import threading
import unittest

from lucy_diagnose.runner import Runner


class RunnerTests(unittest.TestCase):
    def test_missing_command_and_no_elevation(self):
        self.assertIn('not installed', Runner().run('lucy-command-that-does-not-exist').reason)
        self.assertFalse(Runner().run('sudo', 'true').ok)

    def test_argument_is_literal(self):
        result = Runner().run(sys.executable, '-c', 'import sys; print(sys.argv[1])', '$(touch NEVER); *')
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout.strip(), '$(touch NEVER); *')

    def test_timeout_even_when_pipes_close_first(self):
        result = Runner().run(sys.executable, '-c', 'import os,time; os.close(1); os.close(2); time.sleep(10)', timeout=.15)
        self.assertIn('Timed out', result.reason)

    def test_bounded_output(self):
        result = Runner(max_bytes=500).run(sys.executable, '-c', 'print("x" * 20000)')
        self.assertIn('truncated', result.reason)
        self.assertLessEqual(len(result.stdout) + len(result.stderr), 500)

    def test_cancel(self):
        event = threading.Event()
        event.set()
        self.assertIn('cancelled', Runner(event).run(sys.executable, '--version').reason)
