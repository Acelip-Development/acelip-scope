#!/usr/bin/env python3
"""Inventory an extracted AppImage without inferring licenses from filenames.

Every payload file is hashed in local evidence. ELF dependencies, all runtime
manifest source records, Python metadata, and retained notice groups are indexed.
Unmapped artifacts explicitly block component-level redistribution clearance.
"""
import argparse
from collections import Counter
from email.parser import Parser
import hashlib
import json
from pathlib import Path
import re
import subprocess


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def inventory(root):
    runtime = root/'runtime'
    manifest = json.loads((runtime/'manifest.json').read_text())
    files, elfs, notices, python = [], [], [], []
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            files.append({'path': rel, 'link': str(path.readlink())})
            continue
        if not path.is_file():
            continue
        files.append({'path':rel, 'bytes':path.stat().st_size,'sha256':digest(path)})
        with path.open('rb') as f:
            magic=f.read(4)
        if magic==b'\x7fELF':
            dynamic=subprocess.check_output(['readelf','-d',str(path)],text=True,stderr=subprocess.DEVNULL)
            elfs.append({'path':rel,'sha256':files[-1]['sha256'],
                         'needed':re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic),
                         'soname':re.findall(r'\(SONAME\).*?\[(.*?)\]',dynamic),
                         'status':'REVIEW REQUIRED', 'mapping':'No authoritative per-file source ownership in runtime manifest'})
        if path.name=='METADATA' and path.parent.name.endswith('.dist-info'):
            meta=Parser().parsestr(path.read_text(errors='replace'))
            python.append({'name':meta['Name'],'version':meta['Version'],
                           'license':meta['License-Expression'] or meta['License'] or 'REVIEW REQUIRED',
                           'license_files':meta.get_all('License-File',[]),
                           'path':rel,'status':'REVIEW REQUIRED'})
        if '/share/licenses/' in rel or path.name in {'NOTICE','COPYING','LICENSE','copyright'}:
            notices.append(rel)
    groups=Counter()
    for path in (runtime/'share/licenses').rglob('*'):
        if path.is_file():
            parts=path.relative_to(runtime/'share/licenses').parts
            if parts[0] in {'freedesktop-sdk','gnome'}:
                group='/'.join(parts[:2])
            else:group=parts[0]
            groups[group]+=1
    modules=[]
    for module in manifest['modules']:
        modules.append({'name':module['name'],'version':module.get('x-cpe',{}).get('version'),
                        'sources':module.get('sources',[]), 'license':'REVIEW REQUIRED: per-file source grant',
                        'flatpak':'NOT REDISTRIBUTED: separately supplied runtime',
                        'appimage':'REVIEW REQUIRED: manifest includes build and removed components',
                        'status':'REVIEW REQUIRED'})
    return {'scope':'Exact extracted payload; component-source ownership unresolved, not a cleared SBOM',
            'manifest_sha256':digest(runtime/'manifest.json'), 'file_count':len(files),
            'elf_count':len(elfs),'notice_count':len(notices), 'notice_groups':dict(groups),
            'python_distributions':python,'modules':modules,'elfs':elfs,'files':files,'notice_paths':notices}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); result=inventory(args.root)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['file_count','elf_count','notice_count','manifest_sha256']},indent=2))

if __name__=='__main__':main()
