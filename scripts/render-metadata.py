#!/usr/bin/env python3
"""Render/check desktop metadata from the central identity, without invented URLs."""
import argparse
import json
from pathlib import Path
import sys
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lucy_diagnose import __version__
from lucy_diagnose.identity import IDENTITY, APP_ID, DISPLAY_NAME, EXECUTABLE_NAME, TAGLINE


def rendered():
    desktop = f'''[Desktop Entry]
Type=Application
Name={DISPLAY_NAME}
Comment={TAGLINE}
Exec={EXECUTABLE_NAME}
Icon={APP_ID}
Terminal=false
Categories=System;Monitor;
Keywords=diagnostics;health;GPU;audio;system;
StartupNotify=true
StartupWMClass={APP_ID}
'''
    publisher = f'  <developer><name>{escape(IDENTITY["publisher"])}</name></developer>\n' if IDENTITY['publisher'] else ''
    urls = ''.join(f'  <url type="{kind}">{escape(IDENTITY[field])}</url>\n' for field, kind in
                   [('homepage_url','homepage'),('repository_url','vcs-browser'),('support_url','help')]
                   if IDENTITY[field])
    metadata = f'''<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>{APP_ID}</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>{escape(IDENTITY['license'])}</project_license>
  <name>{escape(DISPLAY_NAME)}</name>
  <summary>{escape(TAGLINE.rstrip("."))}</summary>
  <description>
    <p>{escape(DISPLAY_NAME)} is a read-only system diagnostics application with a native GTK interface. Review system health, storage, networking, audio and screen-sharing prerequisites in one dashboard.</p>
    <p>Choose from thirteen themes and explicitly export privacy-filtered Markdown or JSON reports. AI handoff requires fresh consent. Flatpak reports restricted host capabilities and never requests elevated privileges.</p>
  </description>
{publisher}{urls}  <launchable type="desktop-id">{APP_ID}.desktop</launchable>
  <provides><binary>{EXECUTABLE_NAME}</binary></provides>
  <categories><category>System</category><category>Monitor</category></categories>
  <keywords><keyword>diagnostics</keyword><keyword>health</keyword><keyword>GPU</keyword><keyword>audio</keyword></keywords>
  <content_rating type="oars-1.1"/>
  <releases><release version="{__version__}" date="2026-09-26" type="development"/></releases>
  <!-- Final namespace and URLs remain unresolved in identity.json.
       No remote screenshots are declared before there is an approved public host. -->
</component>
'''
    manifest_path = ROOT / 'packaging/flatpak' / (APP_ID + '.json')
    manifest = json.loads((ROOT / 'packaging/flatpak/manifest-template.json').read_text())
    manifest['app-id'] = APP_ID
    manifest['command'] = EXECUTABLE_NAME
    manifest['modules'][0]['name'] = EXECUTABLE_NAME
    return {manifest_path: json.dumps(manifest, indent=2) + '\n', ROOT / 'data' / (APP_ID + '.desktop'): desktop,
            ROOT / 'data' / (APP_ID + '.metainfo.xml'): metadata}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, text in rendered().items():
        if args.check:
            if not path.is_file() or path.read_text() != text:
                raise SystemExit('Metadata drift: run python3 scripts/render-metadata.py')
        else:
            path.write_text(text)


if __name__ == '__main__':
    main()
