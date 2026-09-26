from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lucy_diagnose.models import Support
from lucy_diagnose.platform.linux.sensors import parse_sensors, primary_cpu, read_hwmon, sensor_status, sensor_checks
from lucy_diagnose.platform.linux.telemetry import TelemetrySampler
from lucy_diagnose.runner import Result
from tests.test_collectors import FakeRunner


def fixture():
    return {'k10temp-pci-test': {'Tctl': {'temp1_input': 52}, 'Tdie': {'temp2_input': 50}, 'Tccd1': {'temp3_input': 80}},
            'coretemp-isa-test': {'Package id 0': {'temp1_input': 65}, 'Core 0': {'temp2_input': 85}},
            'discovered-cooler': {'Coolant': {'temp1_input': 35}, 'Pump speed': {'fan1_input': 3000}, 'Fan speed': {'fan2_input': 1200}},
            'nvme-pci-test': {'Composite': {'temp1_input': 40}}, 'spd5118-i2c-test': {'temp1': {'temp1_input': 42}},
            'mlx5-pci-test': {'adapter': {'temp1_input': 49}}, 'amdgpu-pci-test': {'edge': {'temp1_input': 70}}}


class SensorTests(unittest.TestCase):
    def test_k10temp_tctl_preferred_over_hotter_ccd_core_gpu(self):
        selected = primary_cpu(parse_sensors(fixture()))
        self.assertEqual((selected.chip, selected.label, selected.value), ('k10temp-pci-test', 'Tctl', 52))

    def test_tdie_fallback(self):
        data = fixture()
        del data['k10temp-pci-test']['Tctl']
        self.assertEqual(primary_cpu(parse_sensors(data)).label, 'Tdie')

    def test_intel_package_preferred_over_core(self):
        data = {'coretemp-isa-test': fixture()['coretemp-isa-test']}
        self.assertEqual(primary_cpu(parse_sensors(data)).label, 'Package id 0')

    def test_ccd_and_core_fallback(self):
        data = {'k10temp-pci-test': {'Tccd1': {'temp1_input': 58}, 'Tccd2': {'temp2_input': 61}}}
        self.assertEqual(primary_cpu(parse_sensors(data)).label, 'Tccd2')

    def test_cooling_separate_from_cpu(self):
        readings = parse_sensors(fixture())
        cooling = [r for r in readings if r.kind in {'pump', 'fan', 'coolant'}]
        self.assertEqual({r.kind for r in cooling}, {'pump', 'fan', 'coolant'})
        self.assertIsNone(primary_cpu(cooling))
        self.assertEqual(next(r.unit for r in cooling if r.kind == 'pump'), 'RPM')

    def test_storage_memory_network_and_gpu_normalization(self):
        self.assertTrue({'storage', 'memory', 'network', 'gpu'} <= {r.kind for r in parse_sensors(fixture())})

    def test_invalid_and_missing_sensor_values(self):
        data = {'k10temp-test': {'Tctl': {'temp1_input': float('nan')}, 'Tdie': {'temp2_input': True}, 'CCD': {'temp3_input': 900}}}
        self.assertFalse(parse_sensors(data))
        for data in (None, [], {}, {'bad': 'text'}, {'bad': {'temp': 'wrong'}}):
            self.assertIsNone(primary_cpu(parse_sensors(data)))

    def test_hwmon_semantics_match_json_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            chip = root / 'hwmon0'
            chip.mkdir()
            (chip / 'name').write_text('k10temp')
            (chip / 'temp1_label').write_text('Tctl')
            (chip / 'temp1_input').write_text('52000')
            (chip / 'temp2_label').write_text('Tccd1')
            (chip / 'temp2_input').write_text('81000')
            self.assertEqual(primary_cpu(read_hwmon(root)).value, 52)
            sampler = TelemetrySampler({'/proc/stat': 'cpu 10 0 10 80', '/proc/meminfo': 'MemTotal: 1000 kB\nMemAvailable: 500 kB'}.__getitem__, root)
            sample = sampler.sample(FakeRunner())
            self.assertEqual(sample.values['cpu_temp'], 52)
            self.assertIn('k10temp / Tctl', sample.notes['cpu_temp'])

    def test_missing_sensors_command_hwmon_fallback_partial(self):
        with patch('lucy_diagnose.platform.linux.sensors.read_hwmon', return_value=parse_sensors(fixture())):
            readings, coverage = sensor_status(FakeRunner())
        self.assertEqual(coverage, Support.PARTIAL)
        self.assertEqual(primary_cpu(readings).label, 'Tctl')

    def test_no_sensors_is_unavailable_without_fault(self):
        with patch('lucy_diagnose.platform.linux.sensors.read_hwmon', return_value=[]):
            checks = sensor_checks(FakeRunner())
        self.assertTrue(all(c.support == Support.UNAVAILABLE for c in checks))
        self.assertFalse(any(c.status == 'error' for c in checks))
