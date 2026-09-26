#!/usr/bin/env python3
"""Run real metadata validators; report only known unresolved identity warnings.

--release fails any missing public identity or AppStream finding.
Development CI never hides new AppStream errors/warnings.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lucy_diagnose.identity import APP_ID, IDENTITY, unresolved_identity, public_urls


def allowed_tags():
    return ({'url-homepage-missing'} if not public_urls()['homepage_url'] else set()) | ({'developer-info-missing'} if not IDENTITY['publisher'] else set())


def unexpected_issues(output):
    issues = re.findall(r'^([EWI]):\s+.*?:\s*([^\s:]+)\s*$', output, re.M)
    return [(level, tag) for level, tag in issues if level == 'E' or (level == 'W' and tag not in allowed_tags())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'scripts/render-metadata.py'), '--check'], check=True)
    subprocess.run(['desktop-file-validate', str(ROOT / 'data' / (APP_ID + '.desktop'))], check=True)
    result = subprocess.run(['appstreamcli', 'validate', '--no-net', str(ROOT / 'data' / (APP_ID + '.metainfo.xml'))], capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(output)
    if unexpected_issues(output) or (result.returncode and not any(tag in output for tag in allowed_tags())):
        return 1
    if args.release and (result.returncode or unresolved_identity()):
        print('PUBLIC RELEASE BLOCKED: unresolved identity/AppStream metadata')
        return 1
    if result.returncode:
        print('Development metadata checks passed with declared public-release blockers; raw AppStream status remains nonzero')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
