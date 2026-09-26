from copy import deepcopy
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

from lucy_diagnose import __version__
from lucy_diagnose.dashboard import DashboardState, Finding
from lucy_diagnose.exports import export_document, prepare_export, render_markdown
from lucy_diagnose.guidance import guidance_for
from lucy_diagnose.models import Check, Snapshot, Status
from lucy_diagnose.privacy import PrivacyContext, redact_secrets, sanitize_report


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 26, 12, tzinfo=timezone.utc)
        self.context = PrivacyContext('alice', '/home/alice', 'workstation')
        self.check = Check('Disk · /home/alice', '96% full', Status.ERROR,
                           'workstation 192.168.1.2 /home/alice\nAPI_KEY=secret-value\nserial=ABC123\n```\n# untrusted log',
                           source='df', observed_at=self.now)
        self.state = DashboardState()
        self.state.merge(Snapshot('Full Scan', self.now, {'Overview': [Check('Ubuntu version', 'Ubuntu 26.04'), self.check],
                                                        'AI Stack': [Check('Codex', 'codex 1.0')],
                                                        'Discord / Screen Sharing': [Check('ScreenCast portal', 'No sources', Status.WARNING)]}, self.now))

    def test_structure_metadata_and_tool_versions(self):
        document = export_document(self.state, context=self.context, now=self.now)
        self.assertEqual(document['app']['version'], '1.6.0-dev')
        self.assertEqual(document['app']['version'], __version__)
        self.assertEqual(document['scan_types_performed'], ['Full Scan'])
        self.assertEqual(len(document['subsystem_status']), 6)
        self.assertEqual(document['generated_at'], self.now.isoformat())
        self.assertEqual(document['tool_versions'], [{'title': 'Codex', 'summary': 'codex 1.0'}])
        self.assertEqual(document['screen_sharing'][0]['title'], 'ScreenCast portal')
        for finding in document['findings']:
            self.assertTrue({'severity', 'source', 'evidence', 'observed_at', 'explanation'} <= finding.keys())

    def test_sanitized_json_valid_and_original_unchanged(self):
        before = deepcopy(self.state.groups)
        text, name = prepare_export(self.state, 'json', context=self.context)
        data = json.loads(text)
        self.assertEqual(self.state.groups, before)
        for private in ('secret-value', 'ABC123', '/home/alice', 'workstation', '192.168.1.2'):
            self.assertNotIn(private, text)
        self.assertTrue(name.endswith('.json'))
        self.assertEqual(data['app']['name'], 'LUCY Diagnose')
        self.assertTrue(any(f['observed_at'] == self.now.isoformat() for f in data['findings']))

    def test_local_export_keeps_identifiers_but_strips_secrets(self):
        text, _ = prepare_export(self.state, 'json', 'local', self.context)
        self.assertIn('/home/alice', text)
        self.assertIn('192.168.1.2', text)
        self.assertNotIn('secret-value', text)
        self.assertEqual(json.loads(text)['privacy'], 'local-details-secrets-removed')

    def test_invalid_privacy_is_sanitized(self):
        text, _ = prepare_export(self.state, 'json', 'invalid', self.context)
        self.assertNotIn('/home/alice', text)

    def test_markdown_groups_evidence_and_escapes_log_fences(self):
        text, name = prepare_export(self.state, context=self.context)
        self.assertTrue(name.endswith('.md'))
        self.assertIn('### ERROR', text)
        self.assertIn('````text', text)
        self.assertIn('Suggested next step:', text)
        self.assertNotIn('secret-value', text)

    def test_focused_scan_export_retains_old_time_and_unique_scan_types(self):
        later = self.now.replace(hour=13)
        self.state.merge(Snapshot('GPU', later, {'Overview': [Check('GPU', 'RTX test')]}, later))
        data = export_document(self.state, context=self.context)
        self.assertEqual(data['scan_types_performed'], ['Full Scan', 'GPU'])
        disk = next(f for f in data['findings'] if f['title'].startswith('Disk ·'))
        self.assertEqual(disk['observed_at'], self.now.isoformat())

    def test_no_implicit_export_write_or_execution(self):
        with patch('builtins.open', side_effect=AssertionError('Unexpected write')), patch('subprocess.Popen', side_effect=AssertionError('Unexpected execution')):
            prepare_export(self.state, context=self.context)
            for title in ('Failed services / units', 'Disk · /', 'SMART · disk', 'Recent OOM events',
                          'dpkg state', 'Sharing journal errors', 'Internet reachability', 'GPU temperature', 'Custom warning'):
                guidance = guidance_for(Check(title, 'Problem observed', Status.WARNING))
                self.assertTrue(guidance['suggested_next_step'])
                self.assertFalse(guidance['automatic_execution'])
                self.assertFalse(guidance['requires_sudo'])

    def test_every_warning_and_error_has_guidance(self):
        for status in (Status.WARNING, Status.ERROR):
            finding = Finding('System', Check('Unrecognized check', 'Attention', status))
            self.assertTrue(finding.guidance['likely_cause'])
            self.assertIn('Suggested next step', finding.text)
        self.assertIsNone(guidance_for(Check('Passed', 'Fine', Status.OK)))

    def test_private_key_and_credentials_removed_in_local_exports(self):
        raw = '-----BEGIN PRIVATE KEY-----\nprivate material\n-----END PRIVATE KEY-----\nBearer abcdef\nhttps://alice:password@example.com'
        cleaned = redact_secrets(raw)
        for secret in ('private material', 'abcdef', 'alice:password'):
            self.assertNotIn(secret, cleaned)

    def test_product_name_preserved_when_hostname_is_lucy(self):
        data = export_document(self.state, context=PrivacyContext(hostname='LUCY'))
        self.assertEqual(data['app']['name'], 'LUCY Diagnose')

    def test_prefixed_device_identifiers_still_sanitized(self):
        text = 'DMI_PRODUCT_UUID=hardware-id\nDISK_SERIAL=ABC123\nNET_DEVICE_ID=private-device'
        cleaned = sanitize_report(text, self.context)
        for value in ('hardware-id', 'ABC123', 'private-device'):
            self.assertNotIn(value, cleaned)

    def test_unknown_format_rejected(self):
        with self.assertRaises(ValueError):
            prepare_export(self.state, 'html', context=self.context)
