import unittest
from unittest.mock import patch

from lucy_diagnose.analysis import prepare_analysis
from lucy_diagnose.privacy import PrivacyContext, sanitize_report

CONTEXT = PrivacyContext('alice', '/home/alice', 'lucy-host')


class PrivacyTests(unittest.TestCase):
    def test_identifiers_are_redacted_without_mutation(self):
        original = ('alice /home/alice/file /home/bob/private lucy-host alice@example.org '
                    '192.168.1.10 10.2.3.4 172.16.0.1 fe80::1234 fd00::1 aa:bb:cc:dd:ee:ff '
                    '12345678-1234-1234-1234-123456789abc 0123456789abcdef0123456789abcdef\n'
                    'Serial Number: SECRET123\n"serial_number": "DISK987",\n')
        sanitized = sanitize_report(original, CONTEXT)
        for value in ('alice', '/home/bob', 'lucy-host', '192.168.1.10', '10.2.3.4', '172.16.0.1',
                      'fe80::1234', 'fd00::1', 'aa:bb:cc:dd:ee:ff', 'SECRET123', 'DISK987',
                      '12345678-1234-1234-1234-123456789abc', '0123456789abcdef0123456789abcdef'):
            self.assertNotIn(value, sanitized)
        self.assertIn('alice@example.org', original)

    def test_secrets(self):
        raw = ('API_KEY=supersecret\nAuthorization: Bearer abcd1234\n'
               'sk-proj-abcdefghijklmnopqrstuvwxyz\npassword: hunter2\n'
               'https://user:pass@example.com\n'
               '-----BEGIN PRIVATE KEY-----\nkeymaterial\n-----END PRIVATE KEY-----')
        clean = sanitize_report(raw, CONTEXT)
        for value in ('supersecret', 'abcd1234', 'abcdefghijklmnopqrstuvwxyz', 'hunter2', 'user:pass', 'keymaterial'):
            self.assertNotIn(value, clean)

    def test_diagnostic_metrics_survive(self):
        raw = 'NVIDIA RTX 4070 Ti · 55 °C · 120 / 12288 MiB · driver 590.48.01 · public 1.1.1.1'
        self.assertEqual(sanitize_report(raw, CONTEXT), raw)

    def test_external_always_sanitized_local_optional(self):
        with patch('lucy_diagnose.privacy.PrivacyContext.current', return_value=CONTEXT):
            for provider in ('Codex', 'Claude'):
                prompt, _ = prepare_analysis(provider, '/home/alice/private 192.168.0.2')
                self.assertNotIn('alice', prompt)
                self.assertNotIn('192.168.0.2', prompt)
            self.assertIn('/home/alice', prepare_analysis('Ollama', '/home/alice')[0])
            self.assertNotIn('/home/alice', prepare_analysis('Ollama', '/home/alice', redact_local=True)[0])

    def test_model_name_cannot_inject_shell(self):
        import shlex
        _, command = prepare_analysis('Ollama', 'report', model='model; touch BAD')
        self.assertIn('model; touch BAD', shlex.split(command))
        with self.assertRaises(ValueError):
            prepare_analysis('Ollama', 'report', model='--help')
