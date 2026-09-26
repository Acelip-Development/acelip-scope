from datetime import datetime, timezone
import unittest

from lucy_diagnose.models import Check, Snapshot, Status
from lucy_diagnose.reports import render_report


class ReportTests(unittest.TestCase):
    def test_grouping_timestamp_and_partial_scan(self):
        now = datetime.now(timezone.utc)
        snapshot = Snapshot('Full Scan', now, {'Health': [Check('Disk', 'Full', Status.ERROR),
                                                         Check('Journal', 'Permission denied', Status.UNAVAILABLE)]}, now, True)
        report = render_report(snapshot)
        self.assertIn('CANCELLED / PARTIAL', report)
        self.assertIn(now.isoformat(timespec='seconds'), report)
        self.assertIn('[ERROR] Health / Disk: Full', report)
        self.assertIn('UNAVAILABLE CHECKS', report)
        self.assertEqual(snapshot.to_dict()['counts']['error'], 1)
