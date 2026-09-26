"""Fetch a digest-checked OCI userspace for explicit disposable validation.

No runtime, packages, or configuration are installed on the host. Extract only
ordinary files/directories/links beneath a fresh output root. Absolute image
symlinks are made root-relative; device nodes and ownership are not preserved.
This is a userspace test image, not a booted distribution or desktop.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import urllib.error
import urllib.parse
import urllib.request

ACCEPT = ', '.join(('application/vnd.oci.image.index.v1+json',
                    'application/vnd.docker.distribution.manifest.list.v2+json',
                    'application/vnd.oci.image.manifest.v1+json',
                    'application/vnd.docker.distribution.manifest.v2+json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry')
    parser.add_argument('repository')
    parser.add_argument('reference')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = args.output / 'rootfs'
    root.mkdir()
    headers = {'Accept': ACCEPT}

    def request(kind, reference):
        url = f'https://{args.registry}/v2/{args.repository}/{kind}/{reference}'
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)
        except urllib.error.HTTPError as exc:
            if exc.code != 401:
                raise
            challenge = exc.headers.get('WWW-Authenticate', '')
            if not challenge.startswith('Bearer '):
                raise
            fields = urllib.request.parse_keqv_list(urllib.request.parse_http_list(challenge[7:]))
            realm = fields.pop('realm')
            if not realm.startswith('https://'):
                raise ValueError('Refusing insecure token endpoint')
            with urllib.request.urlopen(realm + '?' + urllib.parse.urlencode(fields), timeout=60) as response:
                headers['Authorization'] = 'Bearer ' + json.load(response)['token']
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)

    def manifest(ref):
        with request('manifests', ref) as response:
            raw = response.read()
        digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
        if ref.startswith('sha256:') and ref != digest:
            raise ValueError('Manifest digest mismatch')
        return json.loads(raw), digest

    index, index_digest = manifest(args.reference)
    if 'manifests' in index:
        selected = next(m for m in index['manifests'] if m.get('platform', {}).get('architecture') == 'amd64'
                        and m['platform'].get('os') == 'linux')
        index, digest = manifest(selected['digest'])
    else:
        digest = index_digest
    record = {'registry': args.registry, 'repository': args.repository, 'reference': args.reference,
              'index_digest': index_digest, 'manifest_digest': digest, 'layers': index['layers'],
              'limitations': 'Rootless extracted userspace; image ownership/device nodes not preserved. Not a VM or desktop.'}
    (args.output / 'image.json').write_text(json.dumps(record, indent=2) + '\n')

    def image_filter(member, destination):
        if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
            return None
        if Path(member.name).name.startswith('.wh.'):
            raise ValueError('Whiteout layers require a full OCI runtime; use a base image')
        if member.issym() and member.linkname.startswith('/'):
            member = member.replace(linkname=os.path.relpath(member.linkname.lstrip('/'),
                                                             os.path.dirname(member.name) or '.'))
        return tarfile.data_filter(member, destination)

    for layer in index['layers']:
        expected = layer['digest']
        if not expected.startswith('sha256:'):
            raise ValueError('Unsupported layer digest')
        archive = args.output / (expected.split(':')[1] + '.tar')
        print('Downloading', args.repository, expected, layer['size'], flush=True)
        with request('blobs', expected) as response, archive.open('wb') as target:
            shutil.copyfileobj(response, target)
        with archive.open('rb') as source:
            actual = 'sha256:' + hashlib.file_digest(source, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('Layer digest mismatch')
        with tarfile.open(archive) as source:
            source.extractall(root, filter=image_filter)
        archive.unlink()
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
