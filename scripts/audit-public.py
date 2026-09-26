#!/usr/bin/env python3
"""Audit Git-tracked text without echoing sensitive matches. No network access.

Synthetic identifier fixtures and the documented diagnostic endpoints are
classified explicitly. Credential patterns still run on fixture files.
--history reports historical findings; it never rewrites Git history.
"""
import argparse
import getpass
import hashlib
import ipaddress
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {'tests/test_privacy.py', 'tests/test_exports.py', 'tests/test_collectors.py',
            'tests/test_hardening.py', 'tests/test_packaging.py', 'lucy_diagnose/ui/window.py'}
PROVIDER = re.compile(r'\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,}|AKIA[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b')
ASSIGNMENT = re.compile(r'''(?i)\b(?:[A-Z0-9]+_)*(?:password|passwd|secret|token|api_key|access_key)\s*[:=]\s*["']?([A-Za-z0-9_/+=-]{20,})''')
# Only exact upstream license bytes may carry these public contact addresses.
UPSTREAM_TEXT = {
    'packaging/licenses/freetype/FTL.TXT': '5a5ee54c5001bbad1cdc1a57cc3dd4c42199b2da09d39c7ee41fab002d02967f',
    'packaging/licenses/appimage-runtime/squashfuse/LICENSE': '9e909cc8a8ba27b1a649c964cf9eda37de911f3138c2b64e6d2f01703904ac13',
    'packaging/licenses/appimage-runtime/zlib-static/LICENSE': 'e32ff4e00d9d94930537635291da39e7e612703334bf6fde8c7f1686fe8a45a2',
}
SYNTHETIC_TOKENS = {('tests/test_privacy.py', 'sk-proj-' + 'abcdefghijklmnopqrstuvwxyz')}
HOME = re.compile(r'(?<![\w])/(?:home|Users)/([^/\\\s"\'<>]+)')
EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b')
IPV4 = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
MAC = re.compile(r'(?i)(?<![\w:])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![\w:])')


def scan_text(path, text, username=None):
    findings = []
    upstream = UPSTREAM_TEXT.get(path) == hashlib.sha256(text.encode()).hexdigest()
    username = getpass.getuser() if username is None else username
    for number, line in enumerate(text.splitlines(), 1):
        rules = set()
        if re.search(r'/data/(?:ai|projects)/', line, re.I):
            rules.add('machine-specific-checkout')
        if username not in {'', 'root', 'runner', 'user', 'alice', 'bob'} and re.search(r'(?<![\w-])' + re.escape(username) + r'(?![\w-])', line, re.I):
            rules.add('local-user-name')
        for match in HOME.finditer(line):
            if match[1] not in {'alice', 'bob', 'person', 'validation', 'runner', 'user'}:
                rules.add('personal-home-path')
        for match in EMAIL.finditer(line):
            if not upstream and match[1] not in {'example.org', 'example.com', 'example.test'}:
                rules.add('non-placeholder-email')
        for match in PROVIDER.finditer(line):
            if (path, match[0]) not in SYNTHETIC_TOKENS:
                rules.add('provider-credential')
        if ASSIGNMENT.search(line):
            rules.add('long-credential-assignment')
        if re.match(r'\s*-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----', line):
            rules.add('private-key-block')
        if path not in FIXTURES:
            for match in IPV4.finditer(line):
                try:
                    address = ipaddress.ip_address(match[0])
                except ValueError:
                    continue
                if address.is_private and not (address.is_loopback or address.is_unspecified):
                    rules.add('private-network-address')
            if MAC.search(line):
                rules.add('hardware-address')
        findings += [(number, rule) for rule in sorted(rules)]
    return findings


def tracked():
    names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
    for name in filter(None, names):
        path = ROOT / name
        if path.is_file():
            yield name, path.read_bytes()


def audit(entries):
    failures = []
    for path, data in entries:
        if Path(path).name in {'.env', 'id_rsa', 'id_ed25519', 'book.sqlite'} or path.endswith(('.key', '.p12', '.pfx')):
            failures.append({'path': path, 'line': 1, 'rule': 'private-storage-file'})
        if b'\0' in data:
            continue
        for line, rule in scan_text(path, data.decode('utf-8', errors='replace')):
            failures.append({'path': path, 'line': line, 'rule': rule})
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    entries = list(tracked())
    if args.history:
        objects = subprocess.check_output(['git', '-C', str(ROOT), 'rev-list', '--objects', '--all'], text=True)
        entries = []
        for row in objects.splitlines():
            fields = row.split(' ', 1)
            if len(fields) != 2:
                continue
            sha, path = fields
            kind = subprocess.check_output(['git', '-C', str(ROOT), 'cat-file', '-t', sha], text=True).strip()
            if kind == 'blob':
                entries.append((path, subprocess.check_output(['git', '-C', str(ROOT), 'cat-file', 'blob', sha])))
    findings = audit(entries)
    for finding in findings:
        print(f"{finding['path']}:{finding['line']}: {finding['rule']} (value withheld)")
    print(f"{'HISTORY' if args.history else 'TRACKED TREE'} privacy audit: {len(entries)} files/blobs, {len(findings)} findings")
    return int(bool(findings))


if __name__ == '__main__':
    raise SystemExit(main())
