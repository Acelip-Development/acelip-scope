#!/usr/bin/python3
"""Install exactly two requested user files. No packages, caches, or settings."""

import argparse
from pathlib import Path
import shlex
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from lucy_diagnose.identity import APP_ID, DISPLAY_NAME, EXECUTABLE_NAME, TAGLINE


def desktop_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def integration_files(home):
    launcher = home / '.local/bin' / EXECUTABLE_NAME
    desktop = home / '.local/share/applications' / (APP_ID + '.desktop')
    script = f'#!/bin/sh\n# Managed by {DISPLAY_NAME}\nexec ' + shlex.quote(str(PROJECT / 'scripts/launch.sh')) + ' "$@"\n'
    entry = (f'[Desktop Entry]\n# Managed by {DISPLAY_NAME}\nType=Application\n'
             f'Name={DISPLAY_NAME}\n'
             f'Comment={TAGLINE}\n'
             f'Exec={desktop_quote(launcher)}\n'
             f'Icon={PROJECT / "data/acelip-scope-symbolic.svg"}\n'
             'Terminal=false\nCategories=System;Monitor;\n'
             'Keywords=diagnostics;health;GPU;NVIDIA;Ollama;\nStartupNotify=true\n'
             f'StartupWMClass={APP_ID}\n')
    return {launcher: (script, 0o755), desktop: (entry, 0o644)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    files = integration_files(Path.home())
    # Preflight all destinations before writing either one. Preserve unrelated files.
    for path in files:
        if path.is_symlink() or (path.exists() and not any(marker in path.read_text() for marker in ('# Managed by ' + DISPLAY_NAME, '# Managed by LUCY Diagnose'))):
            parser.error(f'Refusing to overwrite an existing unmanaged file: {path}')
    for path, (contents, mode) in files.items():
        if args.dry_run:
            print(f'{path}\n{contents}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
            path.chmod(mode)
            print(f'Installed {path}')


if __name__ == '__main__':
    main()
