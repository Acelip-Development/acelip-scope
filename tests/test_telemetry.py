from datetime import datetime, timezone
from pathlib import Path
import unittest

from lucy_diagnose.runner import Result
from lucy_diagnose.telemetry import LiveHistory, Sample, TelemetrySampler, cpu_counters, cpu_percent
from tests.test_collectors import FakeRunner


class TelemetryTests(unittest.TestCase):
    def test_cpu_delta_does_not_double_count_guest(self):
        self.assertEqual(cpu_counters('cpu 10 0 10 80 0 0 0 0 8 0\ncpu0 1'), (100, 80))
        self.assertAlmostEqual(cpu_percent((100, 80), (200, 130)), 50)
        self.assertIsNone(cpu_percent(None, (200, 130)))
        self.assertIsNone(cpu_percent((200, 130), (100, 80)))

    def test_only_lightweight_commands_and_missing_gpu_is_a_gap(self):
        data = {'/proc/stat': 'cpu 10 0 10 80 0 0 0 0', '/proc/meminfo': 'MemTotal: 1024 kB\nMemAvailable: 512 kB'}
        runner = FakeRunner()
        sampler = TelemetrySampler(data.__getitem__, Path('/path/that/does/not/exist'))
        first = sampler.sample(runner)
        self.assertIsNone(first.values['cpu'])
        self.assertIsNone(first.values['gpu'])
        self.assertEqual(first.values['ram'], 50)
        data['/proc/stat'] = 'cpu 60 0 10 130 0 0 0 0'
        self.assertEqual(sampler.sample(runner).values['cpu'], 50)
        self.assertEqual({call[0] for call in runner.calls}, {'nvidia-smi'})

    def test_gpu_values_and_pause_epoch_reset(self):
        data = {'/proc/stat': 'cpu 10 0 10 80', '/proc/meminfo': 'MemTotal: 1024 kB\nMemAvailable: 512 kB'}
        runner = FakeRunner({'nvidia-smi': Result((), '40, 55, 1024, 4096', code=0)})
        sampler = TelemetrySampler(data.__getitem__, Path('/path/that/does/not/exist'))
        first = sampler.sample(runner, epoch=0)
        self.assertEqual(first.values['gpu'], 40)
        self.assertEqual(first.values['vram'], 25)
        self.assertEqual(first.values['gpu_temp'], 55)
        data['/proc/stat'] = 'cpu 60 0 10 130'
        self.assertEqual(sampler.sample(runner, epoch=0).values['cpu'], 50)
        data['/proc/stat'] = 'cpu 70 0 10 140'
        self.assertIsNone(sampler.sample(runner, epoch=1).values['cpu'])

    def test_memory_history_is_bounded_and_keeps_missing_values(self):
        history = LiveHistory(limit=2)
        for _ in range(3):
            history.append(Sample(datetime.now(timezone.utc)))
        self.assertEqual(len(history.samples), 2)
        self.assertIsNone(history.samples[-1].values['gpu'])
