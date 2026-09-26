#!/usr/bin/env python3
"""Render conservative release gates from identity and recorded validation facts."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lucy_diagnose.identity import IDENTITY


def evaluate(identity, facts):
    gates = []
    def add(name, passed, detail, scope='rc1'):
        gates.append({'gate': name, 'status': 'PASS' if passed is True else 'BLOCKED', 'detail': detail, 'scope': scope})
    for name, field in [('Application name','display_name'),('Publisher','publisher'),('Tagline','tagline'),
                        ('Application license selected','license')]:
        add(name, bool(identity.get(field)), identity.get(field) or 'Decision remains unresolved')
    for name, field, ready in [('Application ID','application_id', identity.get('application_id_finalized') is True),
                               ('Developer ID','developer_id', bool(identity.get('developer_id'))),
                               ('Target repository namespace','repository_namespace', bool(identity.get('repository_url')))]:
        add(name, bool(identity.get(field)) and ready, identity.get(field) or 'Approved target not set')
    for name, field in [('Remote repository created','remote_repository_created'),
                        ('Homepage reachable','homepage_reachable'),('Support/issues reachable','support_reachable'),
                        ('Security reporting configured','security_reporting_configured')]:
        passed = identity.get(field) is True and (field == 'remote_repository_created' or identity.get('remote_repository_created') is True)
        add(name, passed, facts.get(field + '_detail', 'Remote configuration verified' if passed else 'BLOCKED: remote repository/configuration not yet created or verified'))
    add('Repository public/reachable', identity.get('repository_visibility') == 'public'
        and identity.get('remote_repository_created') is True and identity.get('homepage_reachable') is True,
        facts.get('repository_public_detail', 'Public repository visibility and reachability must both be verified'))
    for name, field in [('CI green on GitHub','ci_remote_passed'),('Automated tests green','tests_passed'),
                        ('Flatpak builds and launches','flatpak_validated'),
                        ('Checksums verified','checksums_verified'),('Builds reproduced','reproduced'),
                        ('Manual save flow tested','manual_save_flow'),('Privacy review complete for current tree','privacy_review'),
                        ('Git-history publication review','history_approved'),
                        ('Source licensing clearance','source_redistribution'),
                        ('Flatpak redistribution clearance','flatpak_redistribution'),
                        ('Source + Flatpak notices','source_flatpak_notices'),
                        ('Screen-sharing status documented','capture_documented'),('Audio status documented','audio_documented'),
                        ('SMART status documented','smart_documented'),('Strict AppStream validation','appstream_clean'),
                        ('README complete','readme_complete'),('CHANGELOG complete','changelog_complete'),
                        ('Clean final Git tree','git_clean'),('Book checkpoint written','book_checkpoint')]:
        add(name, facts.get(field) is True, facts.get(field + '_detail', 'See NAMESPACE-VALIDATION.md for current evidence; earlier validation reports preserve prior scope'))
    add('RC1 source + Flatpak publication authorized', facts.get('rc1_publication_approved') is True
        and facts.get('rc1_distribution') == ['source', 'flatpak'],
        facts.get('rc1_publication_approved_detail', 'Explicit approval must identify source + Flatpak only'))
    for name, field in [('AppImage builds and launches','appimage_validated'),
                        ('AppImage redistribution clearance','appimage_redistribution'),
                        ('AppImage advisory clearance','appimage_advisories'),
                        ('AppImage source/relinking obligations','appimage_source_obligations'),
                        ('AppImage notices','appimage_notices')]:
        add(name, facts.get(field) is True, facts.get(field + '_detail', 'AppImage-only gate; does not apply to the approved source + Flatpak distribution'), 'appimage')
    add('AppImage release', all(facts.get(field) is True for field in
        ('appimage_release_approved','appimage_redistribution','appimage_advisories','appimage_source_obligations','appimage_notices')),
        facts.get('appimage_release_approved_detail', 'WITHHELD: requires separate authorization and all AppImage compliance gates'), 'appimage')
    gates.append({'gate':'Windows/macOS package release', 'status':'NOT APPLICABLE', 'detail':'Diagnostics remain UNSUPPORTED placeholders; Linux-only release candidate', 'scope':'other'})
    return gates


def render(gates):
    text = ('# Release checklist\n\nGenerated by `scripts/release-checklist.py` from central identity and the\n'
            'recorded validation facts. PASS applies only to the stated gate and scope.\n'
            'RC1 distribution is source + Flatpak only. AppImage is withheld; its gates\n'
            'apply only to that excluded format. This checklist does not create a tag\n'
            'or GitHub Release. CI evidence names the commit actually tested.\n\n'
            + ('**PUBLIC RELEASE BLOCKER: Application license not selected.**\n\n'
               if any(g['gate'] == 'Application license selected' and g['status'] == 'BLOCKED' for g in gates) else ''))
    for scope, title in [('rc1','RC1 source + Flatpak'),('appimage','AppImage — withheld from RC1'),('other','Other platforms')]:
        text += f'## {title}\n\n| Gate | Status | Evidence / limit |\n|---|---|---|\n'
        text += ''.join(f'| {g["gate"]} | **{g["status"]}** | {g["detail"]} |\n' for g in gates if g.get('scope','rc1') == scope)
        text += '\n'
    return text.rstrip() + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--facts', type=Path, default=ROOT / 'docs/validation/rc1-release-facts.json')
    args = parser.parse_args()
    facts = json.loads(args.facts.read_text()) if args.facts.exists() else {}
    print(render(evaluate(IDENTITY, facts)), end='')
