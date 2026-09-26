from datetime import datetime, timedelta, timezone
import json
import unittest

from lucy_diagnose.dashboard import DashboardState
from lucy_diagnose.models import Check, Snapshot, Status

NOW = datetime(2026, 9, 26, tzinfo=timezone.utc)


def snapshot(mode, sections, at=NOW):
    return Snapshot(mode, at, sections, at)


class DashboardTests(unittest.TestCase):
    def test_focused_scan_retains_other_scopes_and_observation_time(self):
        state = DashboardState()
        state.merge(snapshot('Quick Scan', {'Overview': [Check('CPU model', 'CPU A'), Check('GPU', 'Old GPU'),
                                                       Check('Disk · /', '50%')], 'Health': [Check('Package database', 'OK', Status.OK)]}))
        state.merge(snapshot('Network', {'Network': [Check('Internet reachability', 'No reply', Status.WARNING)]}))
        state.merge(snapshot('GPU', {'Overview': [Check('GPU', 'New GPU', Status.OK)]}, NOW + timedelta(minutes=1)))
        self.assertEqual(state.find('CPU model').observed_at, NOW)
        self.assertEqual(state.find('GPU').summary, 'New GPU')
        self.assertEqual(state.find('GPU').observed_at, NOW + timedelta(minutes=1))
        self.assertEqual(state.counts()['warning'], 1)

    def test_resolved_findings_are_removed_and_unknown_is_not_healthy(self):
        state = DashboardState()
        state.merge(snapshot('Network', {'Network': [Check('Interface', 'Broken', Status.ERROR)]}))
        self.assertEqual(state.status()[0], Status.ERROR)
        state.merge(snapshot('Network', {'Network': [Check('Interface', 'UP', Status.OK)]}))
        self.assertEqual(state.counts()['error'], 0)
        self.assertEqual(state.status()[0], Status.UNAVAILABLE)
        self.assertEqual(state.status('Network')[0], Status.OK)

    def test_quick_scan_updates_capacity_but_keeps_smart(self):
        state = DashboardState()
        state.merge(snapshot('Storage', {'Storage': [Check('Disk · /old', '90%', Status.WARNING),
                                                     Check('SMART · /dev/sda', 'Passed', Status.OK)]}))
        state.merge(snapshot('Quick Scan', {'Overview': [Check('CPU model', 'CPU'), Check('GPU', 'GPU'), Check('Disk · /', '50%')],
                                           'Health': [Check('Package database', 'OK', Status.OK)]}, NOW + timedelta(minutes=1)))
        self.assertIsNone(state.find('Disk · /old'))
        self.assertEqual(state.find('SMART · /dev/sda').observed_at, NOW)
        self.assertEqual(state.find('Disk · /').observed_at, NOW + timedelta(minutes=1))

    def test_duplicate_capacity_is_counted_once_and_newest_wins(self):
        state = DashboardState()
        state.merge(snapshot('Full Scan', {
            'Overview': [Check('Disk · /', '95%', Status.ERROR, observed_at=NOW)],
            'Health': [Check('Disk · /', '95%', Status.ERROR)],
            'Storage': [Check('Disk · /', '96%', Status.ERROR, observed_at=NOW + timedelta(seconds=1))]}))
        self.assertEqual(state.counts()['error'], 1)
        self.assertEqual(state.find('Disk · /').summary, '96%')

    def test_evidence_metadata_exports_as_json_and_text(self):
        state = DashboardState()
        state.merge(snapshot('GPU', {'Overview': [Check('GPU', 'RTX', Status.OK, 'Device 0')]}))
        finding = state.findings()[0]
        self.assertIn('Source:', finding.text)
        self.assertIn('Explanation:', finding.text)
        self.assertIn('Device 0', finding.text)
        self.assertIn(NOW.isoformat(), json.dumps(state.snapshot().to_dict()))
