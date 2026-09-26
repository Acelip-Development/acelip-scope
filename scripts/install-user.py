#!/usr/bin/python3
"""Install exactly two requested user files. No packages, caches, or settings."""

import argparse
from pathlib import Path
import shlex

PROJECT = Path(__file__).resolve().parents[1]


def desktop_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def integration_files(home):
    launcher = home / '.local/bin/lucy-diagnose'
    desktop = home / '.local/share/applications/io.github.lucydiagnose.LucyDiagnose.desktop'
    script = '#!/bin/sh\n# Managed by LUCY Diagnose\nexec ' + shlex.quote(str(PROJECT / 'scripts/launch.sh')) + ' "$@"\n'
    entry = ('[Desktop Entry]\n# Managed by LUCY Diagnose\nType=Application\nName=LUCY Diagnose\n'
             'Comment=Read-only system and AI stack diagnostics\n'
             f'Exec={desktop_quote(launcher)}\n'
             f'Icon={PROJECT / "data/lucy-diagnose-symbolic.svg"}\n'
             'Terminal=false\nCategories=System;Monitor;\n'
             'Keywords=diagnostics;health;GPU;NVIDIA;Ollama;\nStartupNotify=true\n'
             'StartupWMClass=io.github.lucydiagnose.LucyDiagnose\n')
    return {launcher: (script, 0o755), desktop: (entry, 0o644)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    files = integration_files(Path.home())
    # Preflight all destinations before writing either one. Preserve unrelated files.
    for path in files:
        if path.is_symlink() or (path.exists() and '# Managed by LUCY Diagnose' not in path.read_text()):
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
