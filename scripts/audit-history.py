#!/usr/bin/env python3
"""Read-only, value-withholding audit of every object reachable from all refs.

Output is local review evidence, not an automatic publication approval. Every
blob/path pair from every commit tree is scanned, including deleted/renamed files.
Binary printable strings and raw commit/tag objects are scanned as well.
"""
import argparse
import getpass
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('privacy_audit', ROOT/'scripts/audit-public.py')
privacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(privacy)
PATTERNS = {
    'aws-access-key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'provider-key': privacy.PROVIDER.pattern,
    'private-key': r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----',
    'ssh-public-key': r'\b(?:ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp\d+)\s+[A-Za-z0-9+/]{30,}',
    'authorization': r'(?i)\b(?:bearer|basic)\s+[A-Za-z0-9_+/=-]{8,}',
    'credential-assignment': r'''(?i)\b(?:[\w]+_)*(?:password|passwd|pwd|secret|token|api_key|access_key|cookie|sessionid|session_key)\s*[:=]\s*["']?[^\s,;"']{4,}''',
    'database-userinfo': r'(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s/]+@',
    'jwt': r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
    'private-address': r'\b(?:192\.168\.|10\.|172\.)(?:\d{1,3}\.)?\d',
    'mac': r'(?i)(?<![\w:])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![\w:])',
    'personal-name': r'(?i)\b' + re.escape(getpass.getuser()) + r'\b',
    'home-path': r'/(?:home|Users)/[^\s/]+',
    'checkout': r'(?i)/data/(?:ai|projects)/',
    'nas-private-host': r'(?i)(?:smb://|nfs://|//[^\s/]+/|\b[\w-]+\.(?:lan|local)\b|/mnt/|/media/)',
    'book-config-database': r'(?i)(?:the.?book|book\.sqlite|\b[^\s]+\.(?:sqlite3?|db)\b)',
    'email': privacy.EMAIL.pattern,
    'working-name': r'(?i)lucy',
}

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def scan(data):
    # Latin-1 preserves byte offsets for binary strings; never execute a blob.
    text = data.decode('utf-8', errors='replace')
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule, pattern in PATTERNS.items():
            if re.search(pattern, line):
                hits.append({'line': number, 'rule': rule})
    return hits


def collect():
    commits = git('rev-list', '--all').decode().splitlines()
    occurrences = defaultdict(list)
    for commit in commits:
        for row in git('ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
            if not row:
                continue
            fields, path = row.split(b'\t', 1)
            mode, kind, oid = fields.decode().split()
            if kind == 'blob':
                occurrences[oid].append({'commit': commit, 'path': path.decode()})
    ids = git('rev-list', '--objects', '--all', '--no-object-names').decode().splitlines()
    batch = subprocess.run(['git', '-C', str(ROOT), 'cat-file', '--batch'], input=('\n'.join(ids)+'\n').encode(), capture_output=True, check=True).stdout
    offset = 0
    objects, findings, privacy_findings, binary, generated = [], [], [], [], []
    generated_re = re.compile(r'(?i)(?:\.(?:flatpak|appimage|png|jpe?g|webp|log|sqlite3?|db|zip|tar|gz|xz|7z|pyc|pdf)$|(?:^|/)(?:dist|build|reports|__pycache__)/)')
    for oid in ids:
        end = batch.index(b'\n', offset)
        actual, kind, size = batch[offset:end].decode().split()
        size = int(size); data = batch[end+1:end+1+size]; offset = end+size+2
        assert actual == oid
        objects.append({'oid': oid, 'type': kind, 'bytes': size})
        refs = occurrences.get(oid, [])
        paths = sorted({x['path'] for x in refs})
        if kind not in {'blob', 'commit', 'tag'}:
            continue
        hits = scan(data)
        if hits:
            findings.append({'oid': oid, 'kind': kind, 'paths': paths, 'hits': hits})
        if kind == 'blob':
            for path in paths:
                for line, rule in privacy.scan_text(path, data.decode('utf-8', errors='replace')):
                    privacy_findings.append({'blob': oid, 'path': path, 'line': line, 'rule': rule,
                        'commits': [x['commit'] for x in refs if x['path'] == path]})
            item = {'oid': oid, 'bytes': size, 'paths': paths, 'commits': sorted({x['commit'] for x in refs})}
            if b'\0' in data:
                binary.append(item)
            if any(generated_re.search(p) for p in paths):
                generated.append(item)
    metadata = sorted(set(git('log', '--all', '--format=%an%x09%ae%x09%cn%x09%ce').decode().splitlines()))
    packed = git('cat-file', '--batch-check=%(objectsize:disk)', '--batch-all-objects').decode().splitlines()
    return {'scope': 'All refs; raw commits/tags and every unique blob, every blob/path association; no rewrite',
        'head': git('rev-parse', 'HEAD').decode().strip(), 'commits': commits,
        'refs': git('for-each-ref', '--format=%(refname) %(objectname) %(objecttype)').decode().splitlines(),
        'metadata': [dict(zip(['author_name','author_email','committer_name','committer_email'], row.split('\t'))) for row in metadata],
        'object_counts': dict(Counter(x['type'] for x in objects)), 'reachable_bytes': sum(x['bytes'] for x in objects),
        'all_object_disk_bytes': sum(int(x) for x in packed),
        'largest_blobs': sorted([dict(x, paths=sorted({r['path'] for r in occurrences[x['oid']]})) for x in objects if x['type']=='blob'], key=lambda x:x['bytes'], reverse=True)[:15],
        'binary_blobs': binary, 'generated_candidates': generated, 'privacy_findings': privacy_findings,
        'pattern_counts': dict(Counter(h['rule'] for f in findings for h in f['hits'])), 'pattern_findings': findings,
        'rules': PATTERNS, 'available_scanners': {n: bool(shutil.which(n)) for n in ['gitleaks','trufflehog','detect-secrets']}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['object_counts','reachable_bytes','pattern_counts','available_scanners']}, indent=2))
    print('Privacy findings:', len(result['privacy_findings']), '; binary blobs:',len(result['binary_blobs']))

if __name__ == '__main__':
    main()
