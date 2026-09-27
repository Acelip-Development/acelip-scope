from gi.repository import Gtk
from ..sharing_test import SharingTest
from .widgets import wrap_check_button, set_expander_content, box, label


class SharingPanel(Gtk.Expander):
    def __init__(self, on_result):
        super().__init__(label='Test Screen Sharing · optional manual validation')
        self.test = SharingTest()
        self.on_result = on_result
        body = box()
        set_expander_content(self, body)
        body.append(label('Capture limitation: this build checks prerequisites but cannot inspect captured frames or Discord receiver output. '
                          'This guided test records only your reported result. Acelip Scope opens no capture session and saves no imagery.', None, True))
        self.consent = Gtk.CheckButton(label='I want to perform a manual sharing test now')
        wrap_check_button(self.consent)
        body.append(self.consent)
        self.start = Gtk.Button(label='Start manual test', sensitive=False, halign=Gtk.Align.START)
        self.consent.connect('toggled', lambda button: self.start.set_sensitive(button.get_active() and not self.test.active))
        self.start.connect('clicked', self.begin)
        body.append(self.start)
        self.steps = Gtk.Revealer()
        steps = box()
        steps.append(label('1. Open your existing Discord session and choose Screen Share.\n'
                           '2. Select a harmless window in the system picker if offered.\n'
                           '3. Ask the receiver to verify moving frames. Stop sharing in Discord when finished.\n'
                           '4. Report the outcome below. You control Discord and its capture session.', None, True))
        self.confirm = Gtk.CheckButton(label='The receiver confirmed moving frames')
        wrap_check_button(self.confirm)
        steps.append(self.confirm)
        actions = self.actions = box(Gtk.Orientation.HORIZONTAL, 8)
        self.passed = Gtk.Button(label='PASS', sensitive=False)
        self.confirm.connect('toggled', lambda button: self.passed.set_sensitive(button.get_active() and self.test.active))
        for button, outcome in ((self.passed, 'PASS'), (Gtk.Button(label='FAIL'), 'FAIL'), (Gtk.Button(label='INCONCLUSIVE'), 'INCONCLUSIVE')):
            button.connect('clicked', lambda _, value=outcome: self.finish(value))
            actions.append(button)
        cancel = Gtk.Button(label='Cancel test')
        cancel.connect('clicked', lambda _: self.finish('INCONCLUSIVE'))
        actions.append(cancel)
        steps.append(actions)
        steps.append(label('Cancel closes this checklist only. If you started sharing in Discord, stop it there.', 'caption', True))
        self.steps.set_child(steps)
        body.append(self.steps)
        self.status = label('INCONCLUSIVE · no manual test performed', 'dim-label', True)
        body.append(self.status)

    def begin(self, _):
        self.test.begin(self.consent.get_active())
        self.confirm.set_active(False)
        self.consent.set_active(False)
        self.consent.set_sensitive(False)
        self.start.set_sensitive(False)
        self.steps.set_reveal_child(True)
        self.status.set_text('Manual test in progress · Acelip Scope is not capturing')

    def finish(self, outcome):
        result = self.test.finish(outcome, self.confirm.get_active())
        self.steps.set_reveal_child(False)
        self.consent.set_sensitive(True)
        self.confirm.set_active(False)
        self.status.set_text(result.summary)
        self.on_result(result)
