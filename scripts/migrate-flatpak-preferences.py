#!/usr/bin/env python3
"""Explicit host-side preference copy before launching the new Flatpak ID.

Does not install apps, grant sandbox access, copy reports or remove old settings.
Close both apps before running. Existing destination preferences always win.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lucy_diagnose.identity import APP_ID, EXECUTABLE_NAME
from lucy_diagnose.settings import SettingsStore

# Historical identity, used only by this opt-in host migration helper.
PREVIOUS_APP_ID = 'org.lucydiagnose.LucyDiagnose'


def paths(home):
    base = Path(home) / '.var/app'
    old_config = base / PREVIOUS_APP_ID / 'config'
    return (base / APP_ID / 'config' / EXECUTABLE_NAME / 'preferences.json',
            (old_config / EXECUTABLE_NAME / 'preferences.json',
             old_config / 'lucy-diagnose/preferences.json'))


def reject_symlinks(path):
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError('Refusing a symlinked preference location')


def migrate(home, dry_run=False):
    destination, sources = paths(home)
    reject_symlinks(destination)
    if os.path.lexists(destination):
        return 'Existing final-ID preferences preserved'
    for source in sources:
        reject_symlinks(source)
        if not os.path.lexists(source):
            continue
        # Newer provisional preferences win even when invalid: never silently
        # resurrect older settings or standing consent from an obsolete file.
        values = json.loads(source.read_text())
        if not isinstance(values, dict):
            raise ValueError('Legacy preferences are not a JSON object; source preserved')
        if dry_run:
            return 'Compatible preferences available; no files changed'
        settings = SettingsStore(destination, legacy_path=source, retire_legacy=False)
        try:
            if settings.migration == 'migrated':
                return 'Preferences migrated; old installation preferences preserved'
            if settings.last_error:
                raise OSError('Preference migration could not write the destination; source preserved')
            if destination.is_file():
                return 'Concurrently created final-ID preferences preserved'
            raise OSError('Preference migration incomplete; source preserved')
        finally:
            settings.close()
    return 'No old preferences found; new installs use System defaults'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(), help='Home root (override for isolated acceptance tests)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        print(migrate(args.home, args.dry_run))
    except (OSError, ValueError):
        print('Migration stopped: invalid, inaccessible or unsafe preferences; no legacy file removed.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
