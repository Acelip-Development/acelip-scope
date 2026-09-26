#!/usr/bin/env python3
"""Fetch reviewed inputs only on a disposable GitHub runner. Never used at launch."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('RUNNER_TEMP'):
        raise SystemExit('This setup entry point is for disposable GitHub Actions runners only; use PACKAGING.md locally')
    lock = json.loads((ROOT / 'packaging/runtime-lock.json').read_text())
    arch = 'x86_64'
    ref = f'{lock["runtime"]}/{arch}/{lock["branch"]}'
    def run(*args):
        subprocess.run(args, check=True)
    run('flatpak', '--user', 'remote-add', '--if-not-exists', 'flathub', 'https://dl.flathub.org/repo/flathub.flatpakrepo')
    run('flatpak', '--user', 'install', '--noninteractive', '--no-related', 'flathub', ref)
    run('flatpak', '--user', 'update', '--noninteractive', '--no-related', '--commit=' + lock[arch]['commit'], ref)
    data = urllib.request.urlopen(lock[arch]['appimage_runtime_url'], timeout=60).read()
    if hashlib.sha256(data).hexdigest() != lock[arch]['appimage_runtime_sha256']:
        raise SystemExit('Upstream AppImage runtime bytes differ from lock; reviewed lock update or trusted cache required')
    target = ROOT / 'var/packaging-tools' / ('runtime-' + arch)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(data)


if __name__ == '__main__':
    main()
