"""Application grant, attribution packaging and dependency-gate separation."""
import hashlib
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from lucy_diagnose.identity import IDENTITY, LICENSE, COPYRIGHT, EXECUTABLE_NAME
from lucy_diagnose.runtime import build_info
from tests.test_hardening import script

ROOT = Path(__file__).resolve().parents[1]
package = script('package')
checklist = script('release-checklist')


class LicenseTests(unittest.TestCase):
    def test_exact_standard_license_bytes(self):
        self.assertEqual(hashlib.sha256((ROOT/'LICENSE').read_bytes()).hexdigest(),
                         'cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30')

    def test_canonical_license_and_copyright(self):
        self.assertEqual(LICENSE, 'Apache-2.0')
        self.assertEqual(COPYRIGHT, 'Copyright 2026 Acelip Development')

    def test_appstream_license_does_not_relicense_metadata(self):
        xml = ET.parse(ROOT/'data'/f"{IDENTITY['application_id']}.metainfo.xml")
        self.assertEqual(xml.findtext('project_license'), LICENSE)
        self.assertEqual(xml.findtext('metadata_license'), 'CC0-1.0')

    def test_python_package_spdx_and_distributed_notices(self):
        data=tomllib.loads((ROOT/'pyproject.toml').read_text())
        self.assertEqual(data['project']['license'], LICENSE)
        self.assertEqual(data['project']['license-files'], ['LICENSE','NOTICE'])
        self.assertIn('setuptools>=77', data['build-system']['requires'])

    def test_about_build_information(self):
        self.assertEqual(build_info()['License'], LICENSE)
        self.assertEqual(build_info()['Copyright'], COPYRIGHT)
        text=(ROOT/'lucy_diagnose/ui/window.py').read_text()
        self.assertIn('render_build_info(platform_name=self.platform.name)',text)
        self.assertIn("title='License: ' + LICENSE",(ROOT/'lucy_diagnose/ui/preferences.py').read_text())

    def test_readme_declaration(self):
        text=(ROOT/'README.md').read_text()
        self.assertIn('Acelip Scope is licensed under the Apache License 2.0.',text)
        self.assertIn('[LICENSE](LICENSE)',text)
        self.assertIn(COPYRIGHT,text)

    def test_application_pass_does_not_clear_dependency_gate(self):
        gates={g['gate']:g for g in checklist.evaluate(IDENTITY,{})}
        self.assertEqual(gates['Application license selected']['status'],'PASS')
        self.assertEqual(gates['Application license selected']['detail'],'Apache-2.0')
        self.assertEqual(gates['AppImage source/relinking obligations']['status'],'BLOCKED')
        for name in ['Remote repository created','Homepage reachable','Support/issues reachable','Security reporting configured']:
            self.assertEqual(gates[name]['status'],'PASS')
        for name in ['CI green on GitHub','RC1 source + Flatpak publication authorized','AppImage release']:
            self.assertEqual(gates[name]['status'],'BLOCKED')

    def test_no_current_unresolved_application_license_placeholder(self):
        for file in ['README.md','docs/LICENSING-NOTES.md','docs/PACKAGING.md','docs/RELEASE-CHECKLIST.md','lucy_diagnose/identity.json',f"data/{IDENTITY['application_id']}.metainfo.xml"]:
            text=(ROOT/file).read_text()
            for old in ['LicenseRef-proprietary','Application license not selected','LICENSE — BLOCKED / NOT SELECTED']:
                self.assertNotIn(old,text,file)

    def test_cups_notice_preserved_verbatim(self):
        inventory=json.loads((ROOT/'docs/validation/rc1-license-inventory.json').read_text())
        cups=next(p for p in inventory['notice_files'] if p['path'].endswith('/cups/NOTICE'))
        notice=(ROOT/'NOTICE').read_bytes().split(b'(CUPS 2.4.12):\n\n',1)[1]
        self.assertEqual(hashlib.sha256(notice).hexdigest(),cups['sha256'])
        self.assertIn('GNOME Project',(ROOT/'NOTICE').read_text())

    def test_stage_includes_unmodified_license_and_notice(self):
        with tempfile.TemporaryDirectory() as d, patch.object(package,'provenance',return_value=({'commit':'a'*40,'license':LICENSE},1)):
            package.stage(Path(d),'Flatpak')
            for name in ('LICENSE','NOTICE'):
                self.assertEqual((Path(d)/'share/licenses'/EXECUTABLE_NAME/name).read_bytes(),(ROOT/name).read_bytes())

    def test_provenance_contains_application_license(self):
        data,_=package.provenance()
        self.assertEqual(data['license'],LICENSE)
        self.assertEqual(data['copyright'],COPYRIGHT)


class RuntimeNoticeLinksTests(unittest.TestCase):
    def test_relocated_license_link_preserves_text(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'runtime';base=root/'share/licenses';(base/'common').mkdir(parents=True)
            target=base/'common/LICENSE';target.write_bytes(b'Unmodified upstream notice\n')
            link=base/'COPYING';link.symlink_to('/usr/share/licenses/common/LICENSE')
            package.normalize_license_links(root)
            self.assertFalse(link.readlink().is_absolute())
            root.rename(Path(d)/'moved')
            self.assertEqual((Path(d)/'moved/share/licenses/COPYING').read_bytes(),b'Unmodified upstream notice\n')

    def test_missing_target_fails_without_removing_link(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'share/licenses';base.mkdir(parents=True)
            link=base/'COPYING';link.symlink_to('/usr/share/licenses/common/missing')
            with self.assertRaises(ValueError):package.normalize_license_links(root)
            self.assertTrue(link.is_symlink())

    def test_outside_target_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'share/licenses';base.mkdir(parents=True)
            link=base/'COPYING';link.symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):package.normalize_license_links(root)
            self.assertTrue(link.is_symlink())
