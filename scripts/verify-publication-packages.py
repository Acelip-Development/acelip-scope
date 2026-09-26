#!/usr/bin/env python3
"""Verify license copies and app-only Flatpak contents in actual unpacked artifacts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify(appimage, flatpak, previous=None):
    for base in [appimage/'usr', flatpak/'files']:
        for name in ['LICENSE','NOTICE']:
            if (base/'share/licenses/acelip-scope'/name).read_bytes() != (ROOT/name).read_bytes():
                raise ValueError('Packaged project notice differs: '+name)
        application=base/'share/acelip-scope/lucy_diagnose'
        for p in application.rglob('*'):
            if p.is_file() and p.name!='_build.json':
                if p.read_bytes() != (ROOT/'lucy_diagnose'/p.relative_to(application)).read_bytes():
                    raise ValueError('Application payload differs from source: '+str(p.relative_to(application)))
        build=json.loads((application/'_build.json').read_text())
        if build['dirty']:
            raise ValueError('Package was built from a dirty tree')
    ftl=appimage/'runtime/share/licenses/freedesktop-sdk/freetype/docs/FTL.TXT'
    if ftl.read_bytes() != (ROOT/'packaging/licenses/freetype/FTL.TXT').read_bytes():
        raise ValueError('FreeType license supplement missing or changed')
    license_root=appimage/'runtime/share/licenses'
    links=[p for p in license_root.rglob('*') if p.is_symlink()]
    if not all(not p.readlink().is_absolute() and p.is_file() and p.resolve().is_relative_to(license_root.resolve()) for p in links):
        raise ValueError('Runtime license link broken or escapes package')
    preserved=0
    if previous:
        for p in (previous/'runtime/share/licenses').rglob('*'):
            if p.is_file():
                if p.read_bytes() != (appimage/p.relative_to(previous)).read_bytes():
                    raise ValueError('Upstream notice changed: '+str(p.relative_to(previous)))
                preserved+=1
        for p in (previous/'runtime/lib/python3.13/site-packages').rglob('NOTICE'):
            if p.read_bytes() != (appimage/p.relative_to(previous)).read_bytes():
                raise ValueError('Upstream Python NOTICE changed')
    spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/audit-public.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    flatpak_files=[p for p in (flatpak/'files').rglob('*') if p.is_file()]
    findings=[]
    for p in flatpak_files:
        data=p.read_bytes()
        if data[:4]==b'\x7fELF':
            raise ValueError('Unexpected native library in app-only Flatpak')
        if b'\0' not in data:
            name=p.relative_to(flatpak/'files').as_posix()
            name=name.removeprefix('share/acelip-scope/')
            if name.startswith('validation/'):
                name='scripts/'+name
            findings.extend(audit.scan_text(name,data.decode(errors='replace')))
    if findings:
        raise ValueError('Packaged app privacy findings (values withheld): '+str(len(findings)))
    return {'project_license_notice':'PASS','application_source_bytes':'PASS',
            'freetype_text_sha256':hashlib.sha256(ftl.read_bytes()).hexdigest(),
            'freetype_main_text_gap':'RESOLVED','freetype_full_component_clearance':'REVIEW REQUIRED',
            'relative_license_links':len(links),'upstream_notice_files_preserved':preserved,
            'flatpak_files':len(flatpak_files),'flatpak_native_libraries':0,
            'flatpak_app_privacy_findings':0,'redistribution':{'source_tree':'CLEARED','flatpak':'CLEARED','appimage':'BLOCKED'}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--appimage',type=Path,required=True)
    p.add_argument('--flatpak',type=Path,required=True)
    p.add_argument('--previous-appimage',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=verify(args.appimage,args.flatpak,args.previous_appimage)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
