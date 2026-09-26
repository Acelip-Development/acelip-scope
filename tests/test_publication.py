"""Publication audit coverage and exact upstream license preservation."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.test_hardening import script

ROOT = Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def test_freetype_upstream_bytes_and_acknowledgement(self):
        data = (ROOT/'packaging/licenses/freetype/FTL.TXT').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '5a5ee54c5001bbad1cdc1a57cc3dd4c42199b2da09d39c7ee41fab002d02967f')
        self.assertIn('work of the FreeType Team', (ROOT/'NOTICE').read_text())

    def test_upstream_email_exception_is_exact_and_does_not_hide_credentials(self):
        audit = script('audit-public')
        name = 'packaging/licenses/freetype/FTL.TXT'
        text = (ROOT/name).read_text()
        self.assertEqual(audit.scan_text(name, text, username='runner'), [])
        self.assertTrue(audit.scan_text(name, text+'\nchanged', username='runner'))
        self.assertTrue(audit.scan_text('README.md', text, username='runner'))
        self.assertTrue(audit.scan_text(name, text+'\n-----BEGIN PRIVATE KEY-----', username='runner'))

    def test_history_includes_deleted_renamed_binary_and_commit_messages(self):
        audit = script('audit-history')
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            def git(*args):
                return subprocess.check_output(['git', '-C', d, *args], stderr=subprocess.DEVNULL)
            git('init'); git('config', 'user.name', 'Synthetic Author')
            git('config', 'user.email', 'author@example.org')
            (root/'old.txt').write_text('-----BEGIN PRIVATE KEY-----\nsynthetic\n')
            git('add', '.'); git('commit', '-m', 'initial')
            git('mv', 'old.txt', 'renamed.txt'); git('commit', '-m', 'rename')
            git('rm', 'renamed.txt')
            (root/'binary.dat').write_bytes(b'\0-----BEGIN PRIVATE KEY-----\nsynthetic')
            git('add', '.'); git('commit', '-m', 'message -----BEGIN PRIVATE KEY-----')
            with patch.object(audit, 'ROOT', root):
                result = audit.collect()
            self.assertEqual(result['object_counts']['commit'], 3)
            self.assertEqual(len(result['binary_blobs']), 1)
            self.assertTrue(any(f['kind']=='commit' and any(h['rule']=='private-key' for h in f['hits']) for f in result['pattern_findings']))
            self.assertTrue(any(set(f['paths'])=={'old.txt','renamed.txt'} for f in result['pattern_findings']))

    def test_ignore_local_outputs_but_keep_reproducible_sources(self):
        ignored = ['dist/app.AppImage','build/cache','var/report.json','.venv/bin/python',
                   '.env','.book/state.json','.coverage','exports/report.md','.pytest_cache/state']
        result = subprocess.run(['git','-C',str(ROOT),'check-ignore','--stdin'],
                                input='\n'.join(ignored)+'\n',text=True,capture_output=True)
        self.assertEqual(set(result.stdout.splitlines()),set(ignored))
        result = subprocess.run(['git','-C',str(ROOT),'check-ignore','--no-index','--stdin'],
                                input='tests/fixtures/linux-platforms.json\npackaging/runtime-lock.json\npackaging/licenses/freetype/FTL.TXT\n',text=True,capture_output=True)
        self.assertEqual(result.stdout,'')
