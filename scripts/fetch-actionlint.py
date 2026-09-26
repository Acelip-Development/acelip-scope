#!/usr/bin/env python3
"""Download a pinned dev-only validator into ignored project storage."""
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request

URL = 'https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz'
SHA256 = '8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8'


def main():
    data = urllib.request.urlopen(URL, timeout=60).read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise SystemExit('actionlint checksum mismatch')
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        member = archive.getmember('actionlint')
        if not member.isfile():
            raise SystemExit('Unexpected archive member')
        binary = archive.extractfile(member).read()
    target = Path(__file__).resolve().parents[1] / 'var/tools/actionlint'
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(binary)
    target.chmod(0o755)


if __name__ == '__main__':
    main()
