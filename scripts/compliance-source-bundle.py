#!/usr/bin/env python3
"""Create a deterministic source supplement from verified, already-downloaded archives.

This does not claim to be complete corresponding source for the AppImage.
No downloads, package installation, or source execution are performed.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def bundle(cache,output):
    catalog=(ROOT/'packaging/compliance/source-archives.json').read_bytes()
    data=json.loads(catalog);members={'SOURCE-MANIFEST.json':catalog,
        'README.txt':(data['scope']+'\nSee APPIMAGE-THIRD-PARTY.md for remaining source/relink obligations.\n').encode()}
    for item in data['archives']:
        contents=(cache/item['cache_file']).read_bytes()
        if hashlib.sha256(contents).hexdigest()!=item['sha256']:raise ValueError('Source archive hash mismatch: '+item['name'])
        members['upstream/'+item['archive_file']]=contents
    members['patches/libfuse-mount.c.diff']=(ROOT/'packaging/licenses/appimage-runtime/libfuse/mount.c.diff').read_bytes()
    with output.open('xb') as stream, tarfile.open(fileobj=stream,mode='w',format=tarfile.USTAR_FORMAT) as archive:
        for name,contents in sorted(members.items()):
            info=tarfile.TarInfo(name);info.size=len(contents);info.mode=0o644;info.mtime=0;info.uid=info.gid=0
            archive.addfile(info,io.BytesIO(contents))
    print('Source supplement created; complete corresponding source remains BLOCKED')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();bundle(args.cache,args.output)
