import unittest

from lucy_diagnose.parsers import (cuda_version, flatten_tree, memory_info, nvidia_csv,
                                    smart_summary, temperatures, usage_status, vpn_interfaces)


class ParserTests(unittest.TestCase):
    def test_gpu_csv_and_cuda(self):
        devices = nvidia_csv('"NVIDIA GPU, A", 590.1, 51, 2, 100, 12000, 40.5, [N/A]\n')
        self.assertEqual(devices[0]['name'], 'NVIDIA GPU, A')
        self.assertEqual(devices[0]['fan'], '[N/A]')
        self.assertEqual(cuda_version('| CUDA Version: 13.0 |'), '13.0')
        self.assertIsNone(cuda_version('driver unavailable'))
        with self.assertRaises(ValueError):
            nvidia_csv('bad,row')

    def test_cpu_sensor_does_not_use_gpu_or_nvme(self):
        data = {'nvme-pci': {'Composite': {'temp1_input': 90}},
                'k10temp-pci': {'Tctl': {'temp1_input': 51.5, 'temp1_max': 99}}}
        self.assertEqual(temperatures(data, cpu_only=True), [('k10temp-pci / Tctl', 51.5)])

    def test_memory_and_nested_mounts(self):
        self.assertEqual(memory_info('MemTotal: 1024 kB\nSwapTotal: 0 kB')['MemTotal'], 1048576)
        self.assertEqual([v['name'] for v in flatten_tree([{'name': 'disk', 'children': [{'name': 'part'}]}])], ['disk', 'part'])
        self.assertEqual([usage_status(v) for v in (84, 85, 94, 95)], ['ok', 'warning', 'warning', 'error'])

    def test_smart_and_nvme(self):
        self.assertEqual(smart_summary({'smart_status': {'passed': False}})[0], 'error')
        self.assertEqual(smart_summary({'nvme_smart_health_information_log': {'critical_warning': 1}})[0], 'error')
        status, _, detail = smart_summary({'smart_status': {'passed': True}, 'temperature': {'current': 44}})
        self.assertEqual(status, 'ok')
        self.assertIn('44 °C', detail)
        self.assertEqual(smart_summary({})[0], 'unavailable')

    def test_vpn_heuristic(self):
        self.assertEqual(vpn_interfaces([{'ifname': 'private0', 'linkinfo': {'info_kind': 'wireguard'}},
                                         {'ifname': 'eth0'}, {'ifname': 'tailscale0'}]), ['private0', 'tailscale0'])
