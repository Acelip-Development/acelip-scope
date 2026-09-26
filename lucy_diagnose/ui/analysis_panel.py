"""Inline AI handoffs; no dialogs, command execution, or network requests."""

from gi.repository import Gtk
from ..analysis import prepare_analysis
from .widgets import set_expander_content, accessible_name, box, label, text_view


class AnalysisPanel(Gtk.Expander):
    def __init__(self, copy, save, dashboard_report):
        super().__init__(label='AI explanation · review an explicit handoff')
        self.raw = None
        self.valid = False
        self.copy, self.save = copy, save
        body = box()
        self.scope = label('Choose Explain with AI on a finding, or prepare the dashboard report.', 'dim-label', True)
        body.append(self.scope)
        choices = box(Gtk.Orientation.HORIZONTAL, 8)
        self.provider = Gtk.DropDown.new_from_strings(('Codex · External', 'Claude · External', 'Ollama · Local'))
        accessible_name(self.provider, 'AI handoff provider')
        self.provider.set_hexpand(True)
        choices.append(self.provider)
        whole = Gtk.Button(label='Use dashboard report')
        whole.connect('clicked', lambda _: self.prepare(dashboard_report(), 'Current dashboard report · original observation timestamps retained'))
        choices.append(whole)
        body.append(choices)
        self.model = Gtk.Entry(placeholder_text='Already installed local Ollama model', visible=False)
        accessible_name(self.model, 'Installed local model')
        body.append(self.model)
        self.redact = Gtk.CheckButton(label='Redact the local Ollama report too', visible=False)
        body.append(self.redact)
        self.privacy_note = label('External previews are sanitized. Nothing is sent by Acelip Scope.', 'dim-label', True)
        body.append(self.privacy_note)
        scroll, self.preview = text_view('Choose a finding or the dashboard report to prepare a preview.')
        body.append(scroll)
        self.command_label = label('', 'monospace', True)
        self.command_label.set_selectable(True)
        body.append(self.command_label)
        self.confirm = Gtk.CheckButton(label='I reviewed this exact preview and want to prepare the handoff')
        body.append(self.confirm)
        actions = box(Gtk.Orientation.HORIZONTAL, 8)
        self.copy_prompt = Gtk.Button(label='Copy prompt', sensitive=False)
        self.copy_command = Gtk.Button(label='Copy command', sensitive=False)
        self.save_prompt = Gtk.Button(label='Save prompt…', sensitive=False)
        self.copy_prompt.connect('clicked', lambda _: self.copy(self.prompt))
        self.copy_command.connect('clicked', lambda _: self.copy(self.command))
        self.save_prompt.connect('clicked', lambda _: self.save(self.prompt, 'acelip-scope-analysis.txt'))
        for button in (self.copy_prompt, self.copy_command, self.save_prompt):
            actions.append(button)
        body.append(actions)
        body.append(label('Preview only. Save acelip-scope-analysis.txt in the project, then explicitly run the command there yourself. '
                          'Redaction is best effort; review remaining identifiers. Use an installed local model for Ollama.', 'dim-label', True))
        set_expander_content(self, body)
        self.provider.connect('notify::selected', lambda *_: self.update_preview())
        self.model.connect('changed', lambda _: self.update_preview())
        self.redact.connect('toggled', lambda _: self.update_preview())
        self.confirm.connect('toggled', lambda _: self.consent())

    def prepare(self, report, title):
        self.raw = report
        self.scope.set_text(title)
        self.update_preview()
        self.set_expanded(True)

    def update_preview(self):
        self.confirm.set_active(False)
        provider = ('Codex', 'Claude', 'Ollama')[self.provider.get_selected()]
        external = provider != 'Ollama'
        self.model.set_visible(not external)
        self.redact.set_visible(not external)
        self.privacy_note.set_text('External · sanitized copy. Review all data below; nothing is sent automatically.' if external else
                                  'Local · loopback Ollama. Raw local evidence unless redaction is selected. No inference runs in Acelip Scope.')
        self.valid = False
        if self.raw is not None:
            try:
                self.prompt, self.command = prepare_analysis(provider, self.raw, self.model.get_text() or 'YOUR_INSTALLED_MODEL', self.redact.get_active())
                self.preview.get_buffer().set_text(self.prompt)
                self.command_label.set_text(self.command)
                self.valid = external or bool(self.model.get_text().strip())
            except ValueError as exc:
                self.command_label.set_text(str(exc))
        self.consent()

    def consent(self):
        enabled = self.confirm.get_active() and self.valid
        for button in (self.copy_prompt, self.copy_command, self.save_prompt):
            button.set_sensitive(enabled)
