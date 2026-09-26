#!/usr/bin/env python3
"""Deterministic file-complete inventory, attribution index and CycloneDX 1.6.

Unresolved ownership is explicit. A source manifest/filename association is not
proof of the complete corresponding source or all statically vendored code.
No network, installation, or execution of inventoried binaries is performed.
"""
import argparse
from collections import Counter, defaultdict
import csv
from email.parser import Parser
import fnmatch
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
COMPLIANCE='usr/share/licenses/acelip-scope/compliance/'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def encoded(data):return json.dumps(data,sort_keys=True,indent=2,ensure_ascii=False)+'\n'


def license_assets():
    return json.loads((ROOT/'packaging/compliance/license-assets.json').read_text())['assets']


def install_assets(appdir):
    dest=appdir/'usr/share/licenses/acelip-scope/third-party'
    for record in license_assets():
        source=ROOT/'packaging/licenses'/record['file']
        if sha(source)!=record['sha256']:raise ValueError('Required upstream text changed: '+record['file'])
        target=dest/record['file'];target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    # The hash/provenance catalog travels with the exact excerpts and full texts.
    dest.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'packaging/compliance/license-assets.json',dest/'license-assets.json')


def elf_info(path):
    text=subprocess.check_output(['readelf','-W','-h','-d','-n',str(path)],text=True,stderr=subprocess.DEVNULL)
    get=lambda p:re.findall(p,text)
    return {'needed':get(r'\(NEEDED\).*?\[(.*?)\]'),'soname':get(r'\(SONAME\).*?\[(.*?)\]'),
            'build_ids':get(r'Build ID: ([a-f0-9]+)'),
            'architecture':next(iter(get(r'Machine:\s*(.+)'))),'linkage':'dynamic' if '(NEEDED)' in text else 'static-or-no-needed'}


def modules(runtime):
    result=defaultdict(list)
    for module in json.loads((runtime/'manifest.json').read_text())['modules']:
        if module not in result[module['name']]:result[module['name']].append(module)
    return result


def component(rule,manifest):
    sources=manifest.get(rule['source_module'],[])
    versions=set()
    for m in sources:
        # Source CPE is sometimes more precise than module CPE (e.g. NSS).
        v=next((s.get('x-cpe',{}).get('version') for s in m.get('sources',[]) if s.get('x-cpe',{}).get('version')),None) or m.get('x-cpe',{}).get('version')
        if v:versions.add(v)
    return {'id':rule['id'],'name':rule['id'],'version':next(iter(versions)) if len(versions)==1 else None,
            'version_evidence':'Embedded source manifest; see binary API corroboration for selected libraries',
            'source_package':rule['source_module'],'source_records':sources,
            'upstream':sorted({s['url'] for m in sources for s in m.get('sources',[]) if 'url'in s}),
            'license':rule['license'],'license_version':'See SPDX expression/full per-file grant; NOASSERTION is unresolved',
            'modified':'Downstream patches recorded; complete build attestation unavailable' if any(s.get('type')=='patch' for m in sources for s in m.get('sources',[])) else 'No manifest patch listed; exact build modifications not independently attested',
            'mapping_evidence':rule['mapping_evidence'],'mapping_status':'SOURCE CANDIDATE' if sources else 'REVIEW REQUIRED',
            'required_license_text':'Retain complete upstream texts and per-file exceptions; indexed by notice paths',
            'notice_requirement':'Preserve supplied upstream NOTICE and copyright; no invented attribution',
            'source_requirement':rule['obligation'],'relinking_requirement':'REVIEW REQUIRED for reciprocal components; private modified-library test is not universal compliance',
            'compliance_status':'REVIEW REQUIRED','files':[],'license_paths':[]}


def generate(appdir,artifact=None):
    runtime=appdir/'runtime';manifest=modules(runtime)
    policy=json.loads((ROOT/'packaging/compliance/components.json').read_text())
    launcher=json.loads((ROOT/'packaging/compliance/launcher-components.json').read_text())
    components={r['id']:component(r,manifest) for r in policy['rules']}
    owners={};owner_depth={};python=[]
    for metadata in sorted(runtime.rglob('*.dist-info/METADATA')):
        meta=Parser().parsestr(metadata.read_text(errors='replace'));name=meta['Name'];version=meta['Version']
        if not name or not version:raise ValueError('Incomplete Python metadata')
        rel=metadata.relative_to(appdir).as_posix();id='python:'+rel
        notices=meta.get_all('License-File',[])
        rec={'id':id,'name':name,'version':version,'version_evidence':rel,
             'source_package':name,'upstream':([meta['Home-page']] if meta['Home-page'] else [])+[v.partition(',')[2].strip() for v in meta.get_all('Project-URL',[])],
             'source_records':[],'license':meta['License-Expression'] or meta['License'] or 'NOASSERTION',
             'license_version':'As declared in installed metadata; vendored/per-file exceptions remain',
             'modified':'REVIEW REQUIRED: dist-info does not prove unmodified upstream source',
             'mapping_status':'INSTALLED METADATA','mapping_evidence':'Installed distribution METADATA and RECORD where available',
             'required_license_text':notices,'notice_requirement':'Preserve upstream copyright/NOTICE',
             'source_requirement':'REVIEW REQUIRED; LGPL/MPL vendored terms are not MIT',
             'relinking_requirement':'Source Python can be replaced; native extensions require applicable LGPL review',
             'compliance_status':'REVIEW REQUIRED','files':[],
             'license_paths':[p.relative_to(appdir).as_posix() for p in metadata.parent.rglob('*') if p.is_file() and p.name in notices]}
        components[id]=rec;python.append(id);owner_depth[id]=len(metadata.parent.parent.parts)
        # These GI projects ship metadata without RECORD; their import package
        # names are explicit upstream API identities, not guessed from filenames.
        import_name={'PyGObject':'gi','pycairo':'cairo'}.get(name)
        if import_name:
            for p in (metadata.parent.parent/import_name).rglob('*'):
                if p.is_file():owners.setdefault(p.relative_to(appdir).as_posix(),[]).append(id)
        record=metadata.parent/'RECORD'
        if record.exists():
            for row in csv.reader(record.read_text().splitlines()):
                if not row:continue
                path=posixpath.normpath(metadata.parent.parent.relative_to(appdir).as_posix()+'/'+row[0])
                if not path.startswith('../'):owners.setdefault(path,[]).append(id)
        for p in metadata.parent.rglob('*'):
            if p.is_file():owners.setdefault(p.relative_to(appdir).as_posix(),[]).append(id)
    special={
     'application':('Acelip Scope','Apache-2.0','Project source and exact build provenance; Flatpak also bundles these files'),
     'retained-notices':('Retained upstream runtime license material','NOASSERTION','Notice superset is preserved pending complete ownership; notice presence is not proof component ships'),
     'unmapped':('UNMAPPED PAYLOAD','NOASSERTION','REVIEW REQUIRED: no verified ownership rule; file is not omitted')}
    for id,(name,license,evidence) in special.items():
        components[id]={'id':id,'name':name,'version':None,'license':license,'mapping_evidence':evidence,
                        'mapping_status':'REVIEW REQUIRED' if id!='application' else 'PROJECT SOURCE',
                        'compliance_status':'REVIEW REQUIRED' if id!='application' else 'PASS',
                        'upstream':[],'source_records':[],'modified':'See component source','source_package':None,
                        'required_license_text':'See license index','notice_requirement':'Retain notices',
                        'source_requirement':'REVIEW REQUIRED' if id=='unmapped' else 'See grant',
                        'relinking_requirement':'REVIEW REQUIRED' if id=='unmapped' else 'NOT APPLICABLE','files':[],'license_paths':[]}
    files=[];excluded=[COMPLIANCE+n for n in ['appimage-components.json','appimage-sbom.cdx.json','THIRD-PARTY-LICENSES.md']]
    for path in sorted(appdir.rglob('*')):
        rel=path.relative_to(appdir).as_posix()
        if rel in excluded:
            continue
        if path.is_symlink():item={'path':rel,'kind':'symlink','target':str(path.readlink())}
        elif path.is_file():
            item={'path':rel,'kind':'file','bytes':path.stat().st_size,'sha256':sha(path)}
            with path.open('rb') as f:magic=f.read(4)
            if magic==b'\x7fELF':item['elf']=elf_info(path)
        else:continue
        candidates=sorted(set(owners.get(rel,[])))
        if candidates:
            depth=max(owner_depth[c] for c in candidates)
            candidates=[c for c in candidates if owner_depth[c]==depth]
        if len(candidates)==1:id=candidates[0]
        elif len(candidates)>1:
            id='unmapped';item['candidate_components']=candidates
        elif '/third-party/' in rel:id='retained-notices'
        elif rel.startswith('usr/') or rel in ['AppRun','.DirIcon'] or rel.endswith(('.desktop','.svg')) and not rel.startswith('runtime/'):
            id='application'
        elif '/share/licenses/' in rel:id='retained-notices'
        else:
            matches=[r for r in policy['rules'] if any(fnmatch.fnmatchcase(rel,p) for p in r['patterns']) and not (r['id']=='python' and '/site-packages/' in rel)]
            id=matches[0]['id'] if len(matches)==1 else 'unmapped'
            if len(matches)>1:item['candidate_components']=[m['id'] for m in matches]
        item['component']=id;components[id]['files'].append(rel);files.append(item)
    # Retain only actually represented source families; no ghost manifest modules.
    components={id:c for id,c in components.items() if c['files']}
    for c in components.values():
        if not c['license_paths']:
            stems={c['name'].lower(),Path(c.get('source_package') or '').stem.lower()}
            c['license_paths']=sorted(f['path'] for f in files if '/share/licenses/' in f['path'] and any('/'+stem+'/' in f['path'].lower() for stem in stems if stem))
        c['linkage']=sorted({f['elf']['linkage'] for f in files if f['component']==c['id'] and 'elf'in f}) or ['data/source']
    for entry in launcher['components']:
        c=dict(entry);id='launcher:'+c.pop('id');c.update({'id':id,'name':id.removeprefix('launcher:'),'files':['@appimage-launcher-prefix'],'mapping_status':'BINARY/BUILD EVIDENCE','compliance_status':entry['status'],
            'upstream':[entry['source']['url']],'source_package':entry['source']['name'],
            'source_records':[entry['source']],'required_license_text':'Full texts in third-party/appimage-runtime and original launcher LICENSE',
            'notice_requirement':'Preserve all named copyright and license conditions',
            'source_requirement':entry['source_obligation'],'relinking_requirement':entry['relinking'],
            'license_paths':sorted(f['path'] for f in files if '/third-party/appimage-runtime/'+entry['id']+'/' in f['path'])})
        components[id]=c
    for c in components.values():
        c['redistributed_in_appimage']=True
        c['redistributed_in_flatpak']='Project files only; format-specific launcher excluded' if c['id']=='application' else False
        c.setdefault('license_version','See exact upstream grant/SPDX expression; unresolved exceptions remain')
    unresolved=[f['path'] for f in files if f['component']=='unmapped']
    result={'schema_version':1,'scope':'Every file/link in AppDir except self-describing compliance output; launcher static dependencies separately indexed. Source candidates are not complete corresponding-source attestations.',
            'runtime_manifest_sha256':sha(runtime/'manifest.json'),'launcher_sha256':launcher['launcher_sha256'],
            'artifact_sha256':sha(artifact) if artifact else None,'artifact_name':artifact.name if artifact else None,
            'components':sorted(components.values(),key=lambda c:c['id']),'files':files,
            'coverage':{'files':len(files),'elf_files':sum('elf'in f for f in files),'python_distributions':len(python),
                        'components':len(components),'unmapped_files':len(unresolved),'unmapped_elf_files':sum('elf'in f and f['component']=='unmapped' for f in files),
                        'self_describing_outputs_excluded':sorted(excluded)},
            'source_mapping_status':'BLOCKED' if unresolved else 'REVIEW REQUIRED',
            'redistribution_status':'BLOCKED','unmapped_paths':unresolved,
            'binary_version_evidence':policy['version_evidence'],'freetype_probe':policy['freetype_probe']}
    return result


def sbom(inventory):
    components=[]
    for c in inventory['components']:
        item={'type':'library' if c.get('linkage') not in [['data/source']] else 'data','bom-ref':c['id'],'name':c['name'],
              'properties':[{'name':'acelip:compliance','value':c['compliance_status']},
                            {'name':'acelip:mapping','value':c['mapping_status']} ]}
        if c.get('version'):item['version']=c['version']
        if c['license']!='NOASSERTION':item['licenses']=[{'license':{'name':c['license']}}]
        urls=[u for u in c.get('upstream',[]) if u.startswith('https://')]
        if urls:item['externalReferences']=[{'type':'vcs' if u.endswith('.git') else 'distribution' if any(t in u for t in ['.tar','codeload.github.com']) else 'website','url':u} for u in urls]
        components.append(item)
    dependencies={c['id']:[] for c in inventory['components']}
    for f in inventory['files']:
        id='file:'+f['path'];item={'type':'file','bom-ref':id,'name':f['path']}
        if 'sha256'in f:item['hashes']=[{'alg':'SHA-256','content':f['sha256']}]
        if 'target'in f:item['properties']=[{'name':'acelip:symlink-target','value':f['target']}]
        components.append(item);dependencies[f['component']].append(id)
    root={'type':'application','bom-ref':'acelip-scope-appimage','name':'Acelip Scope','version':'1.0.0-rc1'}
    if inventory['artifact_sha256']:root['hashes']=[{'alg':'SHA-256','content':inventory['artifact_sha256']}]
    dependencies[root['bom-ref']]=sorted(dependencies)
    return {'bomFormat':'CycloneDX','specVersion':'1.6','version':1,
            'metadata':{'component':root,'properties':[{'name':'acelip:scope','value':inventory['scope']},{'name':'acelip:redistribution','value':'BLOCKED'}]},
            'components':components,'dependencies':[{'ref':k,'dependsOn':sorted(v)} for k,v in sorted(dependencies.items())]}


def index(inventory):
    lines=['# Third-party component index','','Generated from the actual AppDir. Third-party copyrights remain upstream.','Source ownership/corresponding-source and reciprocal-license obligations are not cleared by this index.','Flatpak supplies this runtime separately; the listed runtime/launcher libraries are AppImage-only.','Unknown ownership is retained as UNMAPPED PAYLOAD, never omitted.','','| Component | Version | License as evidenced | Upstream | Full texts / evidence | Status |','|---|---|---|---|---|---|']
    for c in inventory['components']:
        paths=', '.join('`'+p+'`' for p in c['license_paths'][:3]) or 'REVIEW REQUIRED: no direct text path mapped'
        upstream=next((u for u in c.get('upstream',[]) if u.startswith('https://')),'See retained copyright text / source mapping')
        lines.append('| '+c['name'].replace('|','/')+' | '+(c.get('version') or 'REVIEW REQUIRED')+' | '+c['license'].replace('|','/')+' | '+upstream+' | '+paths+' | '+c['compliance_status']+' |')
    return '\n'.join(lines)+'\n'


def emit(appdir,out,artifact=None):
    result=generate(appdir,artifact);out.mkdir(parents=True,exist_ok=True)
    (out/'appimage-components.json').write_text(encoded(result))
    (out/'appimage-sbom.cdx.json').write_text(encoded(sbom(result)))
    (out/'THIRD-PARTY-LICENSES.md').write_text(index(result))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('appdir',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--artifact',type=Path);p.add_argument('--install-assets',action='store_true')
    args=p.parse_args()
    if args.install_assets:install_assets(args.appdir)
    result=emit(args.appdir,args.output,args.artifact)
    print(json.dumps(result['coverage'],indent=2));print('Redistribution: BLOCKED; explicit unresolved source/compliance entries remain')

if __name__=='__main__':main()
