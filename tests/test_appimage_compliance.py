"""Fail-closed, deterministic compliance outputs without relying on host runtimes."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import call, patch

from tests.test_hardening import script

compliance=script('appimage-compliance')
ROOT=Path(__file__).resolve().parents[1]


class ElfInfoTests(unittest.TestCase):
    path=Path('libsystemd.so.0.44.0')
    header_dynamic='''ELF Header:
  Machine:                           Advanced Micro Devices X86-64
Dynamic section:
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libcap.so.2]
 0x000000000000000e (SONAME)             Library soname: [libsystemd.so.0]
'''

    def test_normal_elf_preserves_metadata_and_linkage(self):
        for text,needed,soname,linkage in [
            (self.header_dynamic,['libc.so.6','libcap.so.2'],['libsystemd.so.0'],'dynamic'),
            ('Machine: Advanced Micro Devices X86-64\nThere is no dynamic section in this file.\n',[],[],'static-or-no-needed'),
        ]:
            with self.subTest(linkage=linkage), patch.object(compliance.subprocess,'check_output',side_effect=[text,'  Build ID: abcdef0123456789\n']) as readelf:
                self.assertEqual(compliance.elf_info(self.path),{
                    'needed':needed,'soname':soname,'build_ids':['abcdef0123456789'],
                    'architecture':'Advanced Micro Devices X86-64','linkage':linkage})
                self.assertEqual(readelf.call_args_list,[
                    call(['readelf','-W','-h','-d',str(self.path)],text=True,stderr=subprocess.DEVNULL),
                    call(['readelf','-W','-n',str(self.path)],text=True,stderr=subprocess.DEVNULL)])

    def test_note_failure_discards_partial_build_id_but_preserves_required_metadata(self):
        for failure in [
            subprocess.CalledProcessError(1,['readelf','-W','-n',str(self.path)],output='Build ID: deadbeef\n'),
            OSError('Note inspection unavailable'),
        ]:
            with self.subTest(failure=type(failure).__name__), patch.object(compliance.subprocess,'check_output',side_effect=[self.header_dynamic,failure]):
                self.assertEqual(compliance.elf_info(self.path),{
                    'needed':['libc.so.6','libcap.so.2'],'soname':['libsystemd.so.0'],
                    'build_ids':[],'architecture':'Advanced Micro Devices X86-64','linkage':'dynamic'})

    def test_header_dynamic_failure_is_fatal_even_with_partial_valid_output(self):
        failure=subprocess.CalledProcessError(1,['readelf','-W','-h','-d',str(self.path)],output=self.header_dynamic)
        with patch.object(compliance.subprocess,'check_output',side_effect=failure) as readelf:
            with self.assertRaises(subprocess.CalledProcessError) as raised:
                compliance.elf_info(self.path)
            self.assertIs(raised.exception,failure)
            readelf.assert_called_once_with(['readelf','-W','-h','-d',str(self.path)],text=True,stderr=subprocess.DEVNULL)


class AppImageComplianceTests(unittest.TestCase):
    def appdir(self,root):
        runtime=root/'runtime';runtime.mkdir()
        (runtime/'manifest.json').write_text(json.dumps({'modules':[]}))
        (runtime/'unknown-payload').write_bytes(b'Unmapped third-party data\n')
        (runtime/'unknown-link').symlink_to('unknown-payload')
        return root

    def test_every_file_and_link_is_accounted_for_without_inventing_a_version(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.appdir(Path(d));inventory=compliance.generate(root)
            paths={r['path'] for r in inventory['files']}
            self.assertEqual(paths,{'runtime/manifest.json','runtime/unknown-payload','runtime/unknown-link'})
            unknown=next(c for c in inventory['components'] if c['id']=='unmapped')
            self.assertIsNone(unknown['version'])
            self.assertEqual(inventory['source_mapping_status'],'BLOCKED')
            self.assertEqual(inventory['redistribution_status'],'BLOCKED')

    def test_regeneration_in_its_own_payload_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.appdir(Path(d));out=root/compliance.COMPLIANCE
            compliance.emit(root,out)
            before={p.name:p.read_bytes() for p in out.iterdir()}
            compliance.emit(root,out)
            self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
            # An unexpected file in that directory must not disappear from coverage.
            (out/'extra.txt').write_text('Unexpected data')
            self.assertTrue(any(f['path'].endswith('/extra.txt') for f in compliance.generate(root)['files']))

    def test_required_license_assets_fail_closed_and_are_copied_exactly(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.appdir(Path(d));compliance.install_assets(root)
            for asset in compliance.license_assets():
                output=root/'usr/share/licenses/acelip-scope/third-party'/asset['file']
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),asset['sha256'])
            fake={'file':compliance.license_assets()[0]['file'],'sha256':'0'*64}
            with patch.object(compliance,'license_assets',return_value=[fake]):
                with self.assertRaises(ValueError):compliance.install_assets(root)

    def test_nested_python_vendor_metadata_wins_over_parent_record(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.appdir(Path(d));site=root/'runtime/lib/python3.13/site-packages'
            outer=site/'parent-1.dist-info';inner=site/'parent/_vendor/child-2.dist-info'
            outer.mkdir(parents=True);inner.mkdir(parents=True)
            (outer/'METADATA').write_text('Name: parent\nVersion: 1\n')
            (inner/'METADATA').write_text('Name: child\nVersion: 2\nLicense: MIT\n')
            (outer/'RECORD').write_text('parent/_vendor/child-2.dist-info/METADATA,,\n')
            result=compliance.generate(root)
            owners=[c for c in result['components'] if c['name']=='child']
            self.assertEqual(len(owners),1)
            self.assertEqual(owners[0]['version'],'2')
            self.assertIn('runtime/lib/python3.13/site-packages/parent/_vendor/child-2.dist-info/METADATA',owners[0]['files'])

    def test_sbom_file_hashes_dependency_graph_and_no_false_clearance(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.appdir(Path(d));inventory=compliance.generate(root);bom=compliance.sbom(inventory)
            self.assertEqual((bom['bomFormat'],bom['specVersion']),('CycloneDX','1.6'))
            refs={c['bom-ref'] for c in bom['components']}|{bom['metadata']['component']['bom-ref']}
            self.assertEqual(len(refs),len(bom['components'])+1)
            for dependency in bom['dependencies']:
                self.assertIn(dependency['ref'],refs)
                self.assertTrue(set(dependency['dependsOn'])<=refs)
            file=next(c for c in bom['components'] if c['name']=='runtime/unknown-payload')
            self.assertEqual(file['hashes'][0]['content'],hashlib.sha256(b'Unmapped third-party data\n').hexdigest())
            self.assertIn({'name':'acelip:redistribution','value':'BLOCKED'},bom['metadata']['properties'])
