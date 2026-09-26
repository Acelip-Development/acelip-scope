"""Manual sharing validation state. No capture, subprocess, or repair capability."""
from datetime import datetime
from .models import Check, Status


class SharingTest:
    def __init__(self):
        self.active = False
        self.result = None

    def begin(self, consent=False):
        if not consent:
            raise ValueError('Explicit consent is required for each manual test')
        self.active = True
        self.result = None

    def finish(self, outcome, receiver_confirmed=False):
        if not self.active:
            raise ValueError('No active manual sharing test')
        if outcome not in {'PASS', 'FAIL', 'INCONCLUSIVE'}:
            raise ValueError('Unknown outcome')
        if outcome == 'PASS' and not receiver_confirmed:
            raise ValueError('PASS requires confirmation of moving frames at the receiver')
        self.active = False
        self.result = Check('Manual screen-sharing test', outcome + ' · user reported',
                            Status.OK if outcome == 'PASS' else Status.WARNING if outcome == 'FAIL' else Status.INFO,
                            'The user reported this result from an independent Discord sharing attempt. '
                            'Acelip Scope did not capture or inspect frames, audio, or receiver output. '
                            'PASS covers user-confirmed moving frames only; audio is unverified. '
                            'Cancellation and untested sessions are INCONCLUSIVE.',
                            source='Explicit manual test / user report', observed_at=datetime.now().astimezone())
        return self.result

    def cancel(self):
        return self.finish('INCONCLUSIVE') if self.active else None
