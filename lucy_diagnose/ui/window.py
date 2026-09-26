from pathlib import Path
import threading

from gi.repository import Adw, Gio, GLib, Gtk, Pango

from ..analysis import prepare_analysis
from ..models import Status
from ..reports import render_report
from ..runner import Runner
from ..scanner import MODES, SECTION_ORDER, scan

PROJECT = Path(__file__).resolve().parents[2]
ICONS = {'Overview': 'computer-symbolic', 'Health': 'emblem-ok-symbolic', 'Storage': 'drive-harddisk-symbolic',
         'Network': 'network-wired-symbolic', 'AI Stack': 'applications-science-symbolic', 'Reports': 'text-x-generic-symbolic'}
DESCRIPTIONS = {'Overview': 'A snapshot of your Ubuntu workstation.',
                'Health': 'Services, packages, journal errors, and memory pressure.',
                'Storage': 'Devices, mounts, capacity, and available health data.',
                'Network': 'Interfaces, routes, DNS, ports, and reachability.',
                'AI Stack': 'Local tools, model services, and GPU visibility.'}


def label(text='', css=None, wrap=False):
    widget = Gtk.Label(label=text, xalign=0, wrap=wrap)
    if css:
        widget.add_css_class(css)
    return widget


def box(orientation=Gtk.Orientation.VERTICAL, spacing=12):
    return Gtk.Box(orientation=orientation, spacing=spacing)


def padded(widget, amount=24):
    widget.set_margin_top(amount)
    widget.set_margin_bottom(amount)
    widget.set_margin_start(amount)
    widget.set_margin_end(amount)
    return widget


def text_view(text):
    view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
    view.set_left_margin(16)
    view.set_right_margin(16)
    view.set_top_margin(16)
    view.set_bottom_margin(16)
    view.get_buffer().set_text(text)
    scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scroll.set_min_content_height(220)
    scroll.set_child(view)
    scroll.add_css_class('report-view')
    return scroll, view


class LucyWindow(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title='LUCY Diagnose', default_width=1200, default_height=860)
        self.set_size_request(620, 500)
        self.snapshot = None
        self.cancel = threading.Event()
        self.scanning = False
        self.closed = False
        self.smoke_test = application.smoke_test
        self.connect('close-request', self.on_close)
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        root = Adw.ToolbarView()
        self.toast_overlay.set_child(root)
        header = Adw.HeaderBar()
        title = Adw.WindowTitle(title='LUCY Diagnose', subtitle='Your workstation, understood')
        header.set_title_widget(title)
        menu = Gtk.Button(icon_name='sidebar-show-symbolic', tooltip_text='Toggle section navigation')
        menu.connect('clicked', lambda _: self.split.set_show_sidebar(not self.split.get_show_sidebar()))
        header.pack_start(menu)
        badge = label('READ ONLY', 'read-only-badge')
        header.pack_end(badge)
        root.add_top_bar(header)
        self.split = Adw.OverlaySplitView(min_sidebar_width=190, max_sidebar_width=210)
        root.set_content(self.split)
        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 850px'))
        breakpoint.add_setter(self.split, 'collapsed', True)
        breakpoint.add_setter(self.split, 'show-sidebar', False)
        self.add_breakpoint(breakpoint)
        sidebar = padded(box(spacing=24), 16)
        sidebar.add_css_class('sidebar')
        brand = box(spacing=4)
        brand.append(label('L U C Y', 'brand'))
        brand.append(label('DIAGNOSE', 'dim-label'))
        sidebar.append(brand)
        self.navigation = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.navigation.add_css_class('navigation-sidebar')
        for name, icon in ICONS.items():
            row = Gtk.ListBoxRow()
            row.section = name
            content = padded(box(Gtk.Orientation.HORIZONTAL, 12), 10)
            content.append(Gtk.Image.new_from_icon_name(icon))
            content.append(label(name))
            row.set_child(content)
            self.navigation.append(row)
        self.navigation.connect('row-selected', self.on_section)
        sidebar.append(self.navigation)
        spacer = box()
        spacer.set_vexpand(True)
        sidebar.append(spacer)
        sidebar.append(label('LOCAL FIRST', 'caption-heading'))
        sidebar.append(label('On-demand scans.\nNo automatic repairs.\nNo saved scan history.', 'dim-label', True))
        self.split.set_sidebar(sidebar)
        content = box(spacing=0)
        self.split.set_content(content)
        controls = padded(box(spacing=12), 20)
        line = box(Gtk.Orientation.HORIZONTAL, 12)
        self.mode = Gtk.DropDown.new_from_strings(MODES)
        self.mode.set_hexpand(True)
        self.mode.set_tooltip_text('Choose a diagnostic mode; scans run only when requested')
        line.append(self.mode)
        self.scan_button = Gtk.Button(label='Run scan')
        self.scan_button.add_css_class('suggested-action')
        self.scan_button.connect('clicked', lambda _: self.start_scan())
        line.append(self.scan_button)
        self.cancel_button = Gtk.Button(label='Cancel', visible=False)
        self.cancel_button.connect('clicked', self.cancel_scan)
        line.append(self.cancel_button)
        controls.append(line)
        progress_line = box(Gtk.Orientation.HORIZONTAL, 8)
        self.spinner = Gtk.Spinner(visible=False)
        progress_line.append(self.spinner)
        self.scan_status = label('Ready · choose a scan to begin', 'dim-label', True)
        progress_line.append(self.scan_status)
        controls.append(progress_line)
        self.progress = Gtk.ProgressBar(visible=False)
        controls.append(self.progress)
        self.summary = label('Results stay in memory until you choose to save or copy them.', 'dim-label', True)
        controls.append(self.summary)
        content.append(controls)
        content.append(Gtk.Separator())
        self.stack = Gtk.Stack(hexpand=True, vexpand=True, transition_type=Gtk.StackTransitionType.CROSSFADE)
        content.append(self.stack)
        self.flows = {}
        self.empty_labels = {}
        for section in SECTION_ORDER:
            scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
            page = padded(box(spacing=18))
            page.append(label(section, 'title-1'))
            page.append(label(DESCRIPTIONS[section], 'dim-label', True))
            empty = label('No scan results yet. Choose a mode above, then run a scan.', 'dim-label', True)
            page.append(empty)
            self.empty_labels[section] = empty
            flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                               row_spacing=12, column_spacing=12, min_children_per_line=1, max_children_per_line=3)
            flow.set_valign(Gtk.Align.START)
            page.append(flow)
            self.flows[section] = flow
            scroll.set_child(page)
            self.stack.add_named(scroll, section)
        self.build_report_page()
        self.navigation.select_row(self.navigation.get_row_at_index(0))
        if self.smoke_test:
            GLib.idle_add(self.start_scan)
            GLib.timeout_add_seconds(90, self.smoke_timeout)

    def build_report_page(self):
        page = padded(box(spacing=16))
        page.append(label('Reports & analysis', 'title-1'))
        page.append(label('Review your latest scan. Saving and AI handoffs are always explicit.', 'dim-label', True))
        actions = box(Gtk.Orientation.HORIZONTAL, 10)
        self.copy_button = Gtk.Button(label='Copy report', sensitive=False)
        self.copy_button.connect('clicked', lambda _: self.copy_text(render_report(self.snapshot)))
        self.save_button = Gtk.Button(label='Save report…', sensitive=False)
        self.save_button.connect('clicked', lambda _: self.save_text(render_report(self.snapshot), 'lucy-report.txt'))
        actions.append(self.copy_button)
        actions.append(self.save_button)
        page.append(actions)
        choices = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                              row_spacing=8, column_spacing=8, min_children_per_line=1, max_children_per_line=3)
        self.analysis_buttons = []
        for provider in ('Codex', 'Claude', 'Ollama'):
            button = Gtk.Button(sensitive=False)
            body = padded(box(spacing=4), 8)
            body.append(label(f'Analyze with {provider}', 'heading'))
            body.append(label('Local · loopback' if provider == 'Ollama' else 'External · sanitized',
                              'local-label' if provider == 'Ollama' else 'external-label'))
            button.set_child(body)
            button.connect('clicked', lambda _, p=provider: self.show_analysis(p))
            choices.insert(button, -1)
            self.analysis_buttons.append(button)
        page.append(choices)
        page.append(label('AI buttons prepare a preview and command only. V1 does not launch AI clients or send reports.', 'dim-label', True))
        page.append(label('LOCAL REPORT · unredacted', 'caption-heading'))
        scroll, self.report_view = text_view('Run a scan to prepare a report. Nothing is saved automatically.')
        page.append(scroll)
        self.stack.add_named(page, 'Reports')

    def on_section(self, _, row):
        if row:
            self.stack.set_visible_child_name(row.section)
            if self.split.get_collapsed():
                self.split.set_show_sidebar(False)

    def on_close(self, _):
        self.closed = True
        self.cancel.set()
        return False

    def cancel_scan(self, _):
        self.cancel.set()
        self.cancel_button.set_sensitive(False)
        self.scan_status.set_text('Cancelling current checks…')

    def start_scan(self):
        if self.scanning or self.closed:
            return False
        mode = MODES[self.mode.get_selected()]
        self.scanning = True
        self.cancel = threading.Event()
        self.mode.set_sensitive(False)
        self.scan_button.set_sensitive(False)
        self.cancel_button.set_visible(True)
        self.cancel_button.set_sensitive(True)
        self.progress.set_visible(True)
        self.progress.set_fraction(0)
        self.spinner.set_visible(True)
        self.spinner.start()
        self.scan_status.set_text(f'{mode} · collecting read-only diagnostics…')
        def worker():
            result = scan(mode, Runner(self.cancel), lambda name, done, total: GLib.idle_add(self.on_progress, name, done, total))
            GLib.idle_add(self.on_finished, result)
        threading.Thread(target=worker, daemon=True, name='lucy-scan').start()
        return False

    def on_progress(self, name, done, total):
        if not self.closed:
            self.progress.set_fraction(done / total)
            self.scan_status.set_text(f'{name} collected · {done}/{total} sections')
        return False

    def on_finished(self, snapshot):
        if self.closed:
            return False
        self.snapshot = snapshot
        self.scanning = False
        self.mode.set_sensitive(True)
        self.scan_button.set_sensitive(True)
        self.cancel_button.set_visible(False)
        self.progress.set_visible(False)
        self.spinner.stop()
        self.spinner.set_visible(False)
        stamp = snapshot.finished.strftime('%H:%M:%S %Z')
        self.scan_status.set_text(f'{snapshot.mode} · {"Cancelled / partial" if snapshot.cancelled else "Completed"} · {stamp}')
        counts = snapshot.counts()
        self.summary.set_text(f"{counts['error']} errors   ·   {counts['warning']} warnings   ·   {counts['unavailable']} unavailable   ·   "
                              f"{counts['ok'] + counts['info']} passed / info")
        for section, flow in self.flows.items():
            while flow.get_first_child():
                flow.remove(flow.get_first_child())
            checks = snapshot.sections.get(section, [])
            self.empty_labels[section].set_visible(not checks)
            self.empty_labels[section].set_text(f'Not included in {snapshot.mode}. Run Full Scan or the matching focused scan.')
            for check in checks:
                flow.insert(self.check_card(check), -1)
        self.report_view.get_buffer().set_text(render_report(snapshot))
        for button in [self.copy_button, self.save_button, *self.analysis_buttons]:
            button.set_sensitive(True)
        if snapshot.mode in {'Network', 'Storage', 'AI Stack'}:
            self.navigation.select_row(self.navigation.get_row_at_index(list(ICONS).index(snapshot.mode)))
        if self.smoke_test:
            GLib.idle_add(self.exercise_smoke)
        return False

    def check_card(self, check):
        card = box(spacing=10)
        card.set_size_request(200, 148)
        card.add_css_class('diagnostic-card')
        card.add_css_class('status-' + check.status.value)
        title = label(check.title, 'dim-label', True)
        title.set_max_width_chars(24)
        card.append(title)
        value = label(check.summary, 'card-value', True)
        value.set_max_width_chars(20)
        value.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        value.set_lines(3)
        value.set_ellipsize(Pango.EllipsizeMode.END)
        value.set_tooltip_text(check.summary)
        value.set_vexpand(True)
        card.append(value)
        bottom = box(Gtk.Orientation.HORIZONTAL, 8)
        status = label({'ok': '●  Passed', 'info': '●  Info', 'warning': '●  Warning', 'error': '●  Error',
                        'unavailable': '○  Unavailable'}[check.status.value], 'indicator-' + check.status.value)
        status.set_hexpand(True)
        bottom.append(status)
        if check.details:
            detail = Gtk.Button(icon_name='dialog-information-symbolic', tooltip_text=f'Details: {check.title}')
            detail.add_css_class('flat')
            detail.connect('clicked', lambda _: self.show_details(check))
            bottom.append(detail)
        card.append(bottom)
        return card

    def show_details(self, check):
        dialog = Adw.Dialog(title=check.title, content_width=680, content_height=520)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        content = padded(box())
        content.append(label(check.summary, 'title-3', True))
        scroll, _ = text_view(check.details)
        content.append(scroll)
        toolbar.set_content(content)
        dialog.set_child(toolbar)
        dialog.present(self)
        return dialog

    def copy_text(self, text):
        self.get_clipboard().set(text)
        self.toast_overlay.add_toast(Adw.Toast(title='Copied to clipboard'))

    def save_text(self, text, name, parent=None):
        chooser = Gtk.FileDialog(title='Save a local text file', initial_name=name)
        # A chooser is explicit consent to the destination; there is no autosave.
        chooser.set_initial_folder(Gio.File.new_for_path(str(PROJECT)))
        def selected(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file is None:
                    return
                file.replace_contents_bytes_async(GLib.Bytes.new(text.encode()), None, False,
                                                  Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION,
                                                  None, saved)
            except GLib.Error as exc:
                if not exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self.toast_overlay.add_toast(Adw.Toast(title=f'Could not save: {exc.message}'))
        def saved(file, result):
            try:
                file.replace_contents_finish(result)
                self.toast_overlay.add_toast(Adw.Toast(title='File saved'))
            except GLib.Error as exc:
                self.toast_overlay.add_toast(Adw.Toast(title=f'Could not save: {exc.message}'))
        chooser.save(self, None, selected)

    def show_analysis(self, provider):
        if self.snapshot is None:
            return None
        external = provider in {'Codex', 'Claude'}
        raw_report = render_report(self.snapshot)
        dialog = Adw.Dialog(title=f'Analyze with {provider}', content_width=820, content_height=740)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        content = padded(box(spacing=12), 20)
        content.append(label(f'{"External" if external else "Local"} · {provider}', 'title-2'))
        content.append(label('Review the sanitized prompt below before handing it to an external provider. Redaction is best effort; inspect for remaining identifiers.'
                             if external else 'The command targets Ollama on 127.0.0.1. Choose an already installed local model. No model is downloaded by LUCY.', 'dim-label', True))
        local_controls = box(Gtk.Orientation.HORIZONTAL, 12)
        model = Gtk.Entry(placeholder_text='Installed model name, e.g. qwen3:8b', hexpand=True)
        redact = Gtk.CheckButton(label='Redact local report too')
        if not external:
            local_controls.append(model)
            local_controls.append(redact)
            content.append(local_controls)
        prompt, command = prepare_analysis(provider, raw_report)
        scroll, preview = text_view(prompt)
        content.append(scroll)
        command_label = label(command, 'monospace', True)
        command_label.set_selectable(True)
        content.append(command_label)
        content.append(label('V1 preview only: nothing is sent or executed here. Save the exact prompt as lucy-analysis.txt under the project, then explicitly run this command from that folder yourself. '
                             + ('Codex/Claude may use an external service according to their configuration.' if external else 'Use a local model; cloud-backed Ollama models may forward requests externally.'),
                             'dim-label', True))
        confirm = Gtk.CheckButton(label='I reviewed this prompt and want to prepare the handoff')
        content.append(confirm)
        actions = box(Gtk.Orientation.HORIZONTAL, 8)
        copy_prompt = Gtk.Button(label='Copy prompt', sensitive=False)
        copy_command = Gtk.Button(label='Copy command', sensitive=False)
        save_prompt = Gtk.Button(label='Save prompt…', sensitive=False)
        for button in (copy_prompt, copy_command, save_prompt):
            actions.append(button)
        content.append(actions)
        state = {'prompt': prompt, 'command': command, 'valid': external}
        def consent_changed(_):
            for button in (copy_prompt, copy_command, save_prompt):
                button.set_sensitive(confirm.get_active() and state['valid'])
        def update_preview(_):
            confirm.set_active(False)
            try:
                prompt, command = prepare_analysis(provider, raw_report, model.get_text() or 'YOUR_INSTALLED_MODEL', redact.get_active())
                state.update(prompt=prompt, command=command, valid=external or bool(model.get_text().strip()))
                preview.get_buffer().set_text(prompt)
                command_label.set_text(command)
            except ValueError as exc:
                state['valid'] = False
                command_label.set_text(str(exc))
            consent_changed(confirm)
        model.connect('changed', update_preview)
        redact.connect('toggled', update_preview)
        confirm.connect('toggled', consent_changed)
        copy_prompt.connect('clicked', lambda _: self.copy_text(state['prompt']))
        copy_command.connect('clicked', lambda _: self.copy_text(state['command']))
        save_prompt.connect('clicked', lambda _: self.save_text(state['prompt'], 'lucy-analysis.txt'))
        toolbar.set_content(content)
        dialog.set_child(toolbar)
        # Exposed for a native-widget smoke check without any clipboard or disk writes.
        dialog.preview = preview
        dialog.confirm = confirm
        dialog.copy_prompt = copy_prompt
        dialog.present(self)
        return dialog

    def exercise_smoke(self):
        for section in ICONS:
            self.stack.set_visible_child_name(section)
        dialog = self.show_analysis('Codex')
        assert not dialog.copy_prompt.get_sensitive()
        dialog.confirm.set_active(True)
        assert dialog.copy_prompt.get_sensitive()
        dialog.close()
        self.set_default_size(720, 700)
        self.stack.set_visible_child_name('Overview')
        GLib.timeout_add_seconds(2, self.smoke_finish)
        return False

    def smoke_finish(self):
        print('GTK smoke test passed: scan completed, section views rendered, external preview consent verified.')
        self.get_application().smoke_passed = True
        self.close()
        return False

    def smoke_timeout(self):
        if not self.closed:
            print('GTK smoke test timed out', flush=True)
            self.close()
        return False
