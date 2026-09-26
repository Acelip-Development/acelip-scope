"""Public-release behavior regressions; no live services or package tools needed."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

from lucy_diagnose import __version__
from lucy_diagnose.identity import IDENTITY, DISPLAY_NAME, APP_ID, unresolved_identity
from lucy_diagnose.runtime import build_info, Runtime
from lucy_diagnose.privacy import PrivacyContext, sanitize_report, redact_secrets
from lucy_diagnose.errors import unavailable_message
from lucy_diagnose.settings import SettingsStore
from lucy_diagnose.scanner import scan
from lucy_diagnose.commands import Result
from lucy_diagnose.platform.linux.backend import LinuxPlatform

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = script('audit-public')
metadata = script('render-metadata')
validator = script('check-metadata')
checklist = script('release-checklist')


class IdentityTests(unittest.TestCase):
    def test_approved_publisher_preserves_other_unresolved_fields(self):
        self.assertEqual(IDENTITY['publisher'], 'Acelip Development')
        self.assertEqual(IDENTITY['repository_url'], 'https://github.com/Acelip-Development/acelip-scope')
        self.assertTrue(IDENTITY['remote_repository_created'])
        self.assertIn('security_contact', unresolved_identity())
        self.assertIn('security_reporting_configured', unresolved_identity())
        self.assertNotIn('license', unresolved_identity())

    def test_rendered_metadata_uses_central_identity(self):
        rendered = metadata.rendered()
        desktop = rendered[ROOT / 'data' / (APP_ID + '.desktop')]
        self.assertIn('Name=' + DISPLAY_NAME, desktop)
        self.assertIn('Icon=' + APP_ID, desktop)
        self.assertTrue(all(text == path.read_text() for path, text in rendered.items()))

    def test_approved_developer_and_verified_homepage(self):
        text = metadata.rendered()[ROOT / 'data' / (APP_ID + '.metainfo.xml')]
        self.assertIn('<url type="homepage">'+IDENTITY['homepage_url']+'</url>', text)
        self.assertIn('<developer id="io.github.acelip_development"><name>Acelip Development</name></developer>', text)
        self.assertIn(__version__, text)

    def test_new_appstream_errors_are_not_allowed_by_identity_exceptions(self):
        text = 'W: example:~: url-homepage-missing\nE: example:12: description-invalid\n'
        self.assertEqual(validator.unexpected_issues(text), [('W','url-homepage-missing'),('E','description-invalid')])
        with patch.object(validator,'public_urls',return_value={'homepage_url':None}):
            self.assertEqual(validator.unexpected_issues(text), [('E','description-invalid')])

    def test_unrelated_appstream_warning_is_not_suppressed(self):
        self.assertEqual(validator.unexpected_issues('W: example:~: icon-missing\n'), [('W','icon-missing')])

    def test_provenance_architecture_and_reproducible_epoch(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'build.json'
            p.write_text(json.dumps({'commit':'a'*40, 'source_date_epoch':1234567,'architecture':'x86_64'}))
            info = build_info(Runtime('AppImage'), p, 'Linux')
            self.assertEqual(info['Architecture'],'x86_64')
            self.assertEqual(info['Build epoch (SOURCE_DATE_EPOCH)'],'1234567')

    def test_provenance_rejects_path_as_architecture(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'build.json';p.write_text(json.dumps({'architecture':'/tmp/private','source_date_epoch':'/tmp/private'}))
            info=build_info(metadata_path=p)
            self.assertNotIn('/tmp',str(info))


class PrivacyHardeningTests(unittest.TestCase):
    def test_truncated_private_key_redacts_to_end(self):
        raw = '-----BEGIN PRIVATE KEY-----\nunfinished-secret-material'
        self.assertNotIn('unfinished',redact_secrets(raw))

    def test_digest_header_redacts_all_parameters(self):
        clean = redact_secrets('Authorization: Digest username="private", nonce="nonce-value", response="secret-value"\nCPU: 20')
        self.assertNotIn('nonce-value',clean)
        self.assertNotIn('secret-value',clean)
        self.assertIn('CPU: 20',clean)

    def test_proxy_authorization_header(self):
        self.assertNotIn('opaque-credential',redact_secrets('Proxy-Authorization: Custom opaque-credential'))

    def test_cookie_header_removes_multiple_cookies(self):
        clean=redact_secrets('Set-Cookie: session=opaque; refresh=more-secret; Secure')
        self.assertNotIn('opaque',clean)
        self.assertNotIn('more-secret',clean)

    def test_private_key_environment_assignment(self):
        self.assertNotIn('inline-secret',redact_secrets('SERVICE_PRIVATE_KEY=inline-secret'))

    def test_connection_string_environment(self):
        self.assertNotIn('server-private',redact_secrets('CONNECTION_STRING=server-private;credential=topsecret'))

    def test_token_only_uri_credentials(self):
        self.assertNotIn('opaque-token',redact_secrets('https://opaque-token@example.org/api'))

    def test_public_host_ip_is_masked_but_probe_endpoint_is_kept(self):
        value=sanitize_report('8.8.4.4 1.1.1.1',PrivacyContext())
        self.assertNotIn('8.8.4.4',value)
        self.assertIn('1.1.1.1',value)

    def test_private_mount_paths_are_masked(self):
        clean=sanitize_report('/mnt/private-nas/photos /media/alice/PRIVATE',PrivacyContext())
        self.assertNotIn('private-nas',clean)
        self.assertNotIn('PRIVATE',clean)

    def test_windows_home_and_unc_share_are_masked(self):
        clean=sanitize_report(r'C:\Users\alice\file \\server\private-share\file',PrivacyContext())
        self.assertNotIn('alice',clean)
        self.assertNotIn('private-share',clean)


class RepositoryAuditTests(unittest.TestCase):
    def test_personal_checkout_path_detected_without_echo(self):
        value='/data/'+'ai/Projects/private'
        self.assertEqual(audit.scan_text('README.md',value,username='runner')[0][1],'machine-specific-checkout')

    def test_local_username_detected(self):
        self.assertEqual(audit.scan_text('README.md','developer_person',username='developer_person')[0][1],'local-user-name')

    def test_product_name_is_not_a_hostname_leak(self):
        self.assertEqual(audit.scan_text('README.md',DISPLAY_NAME,username='runner'),[])

    def test_private_ip_in_docs_detected(self):
        self.assertTrue(audit.scan_text('README.md','192.168.15.42',username='runner'))

    def test_synthetic_ip_fixture_allowed(self):
        self.assertEqual(audit.scan_text('tests/test_privacy.py','192.168.15.42',username='runner'),[])

    def test_real_credential_pattern_still_checked_in_fixtures(self):
        value='ghp_'+'a'*30
        findings=audit.scan_text('tests/test_privacy.py',value,username='runner')
        self.assertIn((1,'provider-credential'),findings)

    def test_long_generic_secret_is_detected(self):
        value='SERVICE_TOKEN=' + 'randomvalue' * 4
        self.assertIn((1,'long-credential-assignment'),audit.scan_text('example.py',value,username='runner'))

    def test_private_binary_storage_is_not_ignored(self):
        findings=audit.audit([('credentials.p12',bytes([0,1,2]))])
        self.assertEqual(findings[0]['rule'],'private-storage-file')

    def test_placeholder_email_allowed(self):
        self.assertEqual(audit.scan_text('README.md','person@example.org',username='runner'),[])

    def test_nonplaceholder_email_flagged(self):
        self.assertTrue(audit.scan_text('README.md','person' + '@' + 'private.invalid',username='runner'))


class FirstRunAndErrorsTests(unittest.TestCase):
    def test_clean_preferences_need_no_network_or_configuration(self):
        with tempfile.TemporaryDirectory() as d, patch.object(socket,'socket',side_effect=AssertionError('network prohibited')):
            settings=SettingsStore(Path(d)/'preferences.json')
            self.assertEqual(settings.get('theme'),'system')
            self.assertEqual(settings.get('report_privacy'),'sanitized')
            self.assertFalse(settings.path.exists())
            settings.close()

    def test_quick_scan_works_without_network(self):
        class OfflineRunner:
            cancel=threading.Event()
            def run(self,*args,**kwargs):
                return Result(tuple(args),problem='Command not installed')
        with patch.object(socket,'socket',side_effect=AssertionError('network prohibited')):
            result=scan('Quick Scan',runner=OfflineRunner(),platform=LinuxPlatform())
        self.assertTrue(result.sections['Overview'])
        self.assertTrue(result.sections['Health'])
        self.assertFalse(any('Collector failed' in c.summary for rows in result.sections.values() for c in rows))

    def test_timeout_gives_actionable_message(self):
        self.assertIn('try again',unavailable_message('Timed out after 7 seconds'))

    def test_disconnection_does_not_mean_global_diagnostic_failure(self):
        self.assertIn('other diagnostics can continue',unavailable_message('Network is unreachable'))

    def test_internal_exception_name_not_primary_message(self):
        message=unavailable_message('FileNotFoundError: missing')
        self.assertNotIn('FileNotFoundError',message)
        self.assertIn('health is unknown',message)


class ReleaseGateTests(unittest.TestCase):
    def test_absent_evidence_never_means_pass(self):
        gates=checklist.evaluate({}, {})
        self.assertFalse(any(g['status']=='PASS' for g in gates))

    def test_local_tests_do_not_mark_remote_ci_green(self):
        gates={g['gate']:g for g in checklist.evaluate(IDENTITY,{'tests_passed':True})}
        self.assertEqual(gates['Automated tests green']['status'],'PASS')
        self.assertEqual(gates['CI green on GitHub']['status'],'BLOCKED')

    def test_license_decision_cannot_be_overridden_by_test_evidence(self):
        gates={g['gate']:g for g in checklist.evaluate({**IDENTITY, 'license': None},{'license':True})}
        self.assertEqual(gates['Application license selected']['status'],'BLOCKED')

    def test_checklist_has_only_declared_statuses(self):
        self.assertTrue(all(g['status'] in {'PASS','BLOCKED','NOT APPLICABLE'} for g in checklist.evaluate(IDENTITY,{})))

    def test_workflows_are_read_only_and_actions_pinned(self):
        try:
            import yaml
        except ImportError:
            self.skipTest('Optional PyYAML for workflow structure checks')
        import re
        for path in (ROOT/'.github/workflows').glob('*.yml'):
            data=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
            self.assertEqual(data['permissions'],{'contents':'read'})
            self.assertNotIn('pull_request_target',data['on'])
            for job in data['jobs'].values():
                for step in job['steps']:
                    if 'uses' in step:
                        self.assertRegex(step['uses'],r'@[0-9a-f]{40}$')
        package=(ROOT/'.github/workflows/package.yml').read_text()
        self.assertNotIn('gh release',package)
        self.assertIn('cmp dist/SHA256SUMS',package)
