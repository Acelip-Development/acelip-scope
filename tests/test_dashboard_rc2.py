"""Presentation policy exercised against retained multi-scan observations."""
from datetime import timedelta
import unittest

from lucy_diagnose.dashboard import DashboardState, SUBSYSTEMS
from lucy_diagnose.models import Check, Status, Support
from tests.test_dashboard import NOW, snapshot


def sample_state():
    state = DashboardState()
    state.merge(snapshot('Full Scan', {
        'Overview': [Check('CPU temperature', '51 °C', details='Primary CPU sensor: k10temp / Tctl\nCPU CCD: 49 °C', source='sample hwmon'),
                     Check('Cooling telemetry', '3 cooling readings', details='Coolant: 32 °C\nPump: 2100 RPM\nFan: 900 RPM'),
                     Check('GPU', 'This diagnostic is restricted by the Flatpak sandbox.', Status.UNAVAILABLE)],
        'Health': [Check('Failed services / units', '1 failed unit', Status.ERROR, 'example.service failed', count=1),
                   Check('Recent journal errors', '2 visible entries', Status.WARNING, 'Sample journal evidence', count=2)],
        'Network': [Check('Internet reachability', 'No response', Status.WARNING, 'Single sample ICMP probe')],
        'Storage': [Check('Disk · /', '88% used', Status.WARNING, 'Sample filesystem'),
                    Check('SMART · sample disk', 'Permission restricted', Status.UNAVAILABLE)],
        'AI Stack': [Check('Ollama service', 'Not installed', Status.INFO)],
        'Discord / Screen Sharing': [Check('ScreenCast portal', 'No sources advertised', Status.INFO, support=Support.PARTIAL)],
    }))
    return state


class RC2PresentationTests(unittest.TestCase):
    def test_top_three_excludes_coverage_and_orders_critical_before_warning(self):
        state = sample_state()
        preview = state.attention_preview()
        self.assertEqual(len(preview), 3)
        self.assertEqual([f.check.status for f in preview], [Status.ERROR, Status.WARNING, Status.WARNING])
        self.assertEqual(state.counts(), {'ok': 0, 'info': 4, 'warning': 3, 'error': 1, 'unavailable': 2})
        self.assertEqual(len(state.findings()), 10)

    def test_all_order_keeps_info_above_expected_unavailable_without_promotion(self):
        findings = sample_state().filtered_findings(1)
        self.assertEqual([f.check.status for f in findings],
                         [Status.ERROR] + [Status.WARNING]*3 + [Status.INFO]*4 + [Status.UNAVAILABLE]*2)
        gpu = next(f for f in findings if f.check.title == 'GPU')
        self.assertEqual(gpu.check.support, Support.UNAVAILABLE)

    def test_actionable_default_omits_info_and_unavailable_and_can_be_empty(self):
        state = DashboardState()
        state.merge(snapshot('Network', {'Network': [Check('Coverage', 'Restricted', Status.UNAVAILABLE),
                                                   Check('Note', 'Observed', Status.INFO)]}))
        self.assertEqual(state.filtered_findings(), [])
        self.assertEqual(state.attention_preview(), [])
        self.assertEqual(state.status('Network')[0], Status.UNAVAILABLE)

    def test_info_unavailable_and_scope_filters_do_not_mutate_scan(self):
        state = sample_state()
        before = state.snapshot().to_dict()
        self.assertEqual(len(state.filtered_findings(4)), 4)
        self.assertEqual(len(state.filtered_findings(5)), 2)
        self.assertEqual([f.check.title for f in state.filtered_findings(5, 'Storage')], ['SMART · sample disk'])
        self.assertEqual([f.check.title for f in state.filtered_findings(0, 'Network')], ['Internet reachability'])
        self.assertEqual(state.snapshot().to_dict(), before)

    def test_focused_refresh_keeps_other_details_sources_and_timestamps(self):
        state = sample_state()
        original = state.find('CPU temperature')
        state.merge(snapshot('Network', {'Network': [Check('Internet reachability', 'Reply', Status.OK)]}, NOW+timedelta(minutes=2)))
        self.assertEqual(state.find('CPU temperature'), original)
        self.assertEqual(state.find('CPU temperature').observed_at, NOW)
        for index in range(7): state.filtered_findings(index)
        self.assertEqual(state.find('CPU temperature').details, original.details)
        self.assertEqual(state.find('Internet reachability').observed_at, NOW+timedelta(minutes=2))
        self.assertEqual(len(state.attention_preview()), 3)

    def test_concise_cards_keep_cooling_distinct_and_preserve_full_sensor_evidence(self):
        state = sample_state()
        for name in SUBSYSTEMS:
            self.assertLessEqual(len(state.subsystem_summary(name).splitlines()), 2)
        self.assertIn('Cooling: 3 readings', state.subsystem_summary('System'))
        self.assertNotIn('51', state.subsystem_summary('System'))
        self.assertIn('k10temp / Tctl', state.find('CPU temperature').details)
        self.assertIn('Pump: 2100 RPM', state.find('Cooling telemetry').details)
        self.assertEqual(state.subsystem_summary('GPU / NVIDIA'), 'Flatpak host access restricted\n1 unavailable')
        self.assertIn('88% busiest filesystem', state.subsystem_summary('Storage'))

    def test_remediation_copy_evidence_survives_presentation_filters(self):
        state = sample_state()
        finding = state.filtered_findings(2)[0]
        for text in ('example.service', 'What happened:', 'Why it matters:', 'Likely cause:',
                     'Suggested next step:', 'Source:', 'Observed:', NOW.isoformat(timespec='seconds')):
            self.assertIn(text, finding.text)
        self.assertEqual(state.filtered_findings(1)[0].text, finding.text)
