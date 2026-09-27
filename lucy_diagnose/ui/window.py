"""One application window for metrics, subsystem summaries, and findings."""
import logging
from ..identity import DISPLAY_NAME, PUBLISHER, TAGLINE
from pathlib import Path
import threading
from gi.repository import Adw, Gio, GLib, Gtk, Pango

from ..dashboard import DashboardState, SUBSYSTEMS, SEVERITIES, finding_key
from ..models import Status
from ..guidance import guidance_text
from ..reports import render_report
from ..platform.detect import get_platform
from ..scanner import MODES, scan
from ..telemetry import LiveHistory, METRICS
from .analysis_panel import AnalysisPanel
from .preferences import PreferencesPanel
from .sharing_panel import SharingPanel
from .export_panel import ExportPanel
from .widgets import set_expander_content, accessible_name, GaugeCard, GpuMetricCard, box, clear, label, padded, text_view

PROJECT = Path(__file__).resolve().parents[2]
ICONS = ('computer-symbolic', 'video-display-symbolic', 'network-wired-symbolic', 'drive-harddisk-symbolic', 'applications-science-symbolic', 'camera-video-symbolic')
SEVERITY_LABEL = {Status.ERROR: '✕ Critical', Status.WARNING: '⚠ Warning',
                  Status.INFO: 'ⓘ Info', Status.UNAVAILABLE: '○ Unavailable', Status.OK: '✓ Passed'}


class LucyWindow(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title=DISPLAY_NAME, default_width=1740, default_height=1000)
        self.set_size_request(480, 480)
        self.platform = get_platform()
        self.state, self.history, self.sampler = DashboardState(), LiveHistory(), self.platform.create_sampler()
        self.cancel, self.live_cancel = threading.Event(), threading.Event()
        self.scanning = self.closed = self.live_busy = False
        self.live_generation, self.live_timer = 0, None
        self.expanded_findings = set()
        self.smoke_test = application.smoke_test
        self.connect('close-request', self.on_close)
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        toolbar = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar)
        header = Adw.HeaderBar()
        self.window_title = Adw.WindowTitle(title=DISPLAY_NAME, subtitle=TAGLINE)
        header.set_title_widget(self.window_title)
        header.pack_end(label('READ ONLY', 'read-only-badge'))
        preferences = Gtk.Button(icon_name='emblem-system-symbolic', tooltip_text='Preferences')
        preferences.connect('clicked', lambda _: self.show_preferences())
        accessible_name(preferences, 'Preferences')
        header.pack_end(preferences)
        about = Gtk.Button(icon_name='help-about-symbolic', tooltip_text='About / build information')
        about.connect('clicked', lambda _: self.show_about())
        accessible_name(about, 'About and build information')
        header.pack_end(about)
        toolbar.add_top_bar(header)
        self.pages = Gtk.Stack(hhomogeneous=False, vhomogeneous=False,
                               transition_type=Gtk.StackTransitionType.NONE)
        self.navigation = Gtk.StackSwitcher(stack=self.pages, halign=Gtk.Align.CENTER)
        accessible_name(self.navigation, 'Main views: Overview, Findings, Reports')
        padded(self.navigation, 6)
        toolbar.add_top_bar(self.navigation)
        toolbar.set_content(self.pages)
        self.page_contents, self.page_scrolls = {}, {}
        for name, title in (('overview', 'Overview'), ('findings', 'Findings'), ('reports', 'Reports')):
            scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
            content = padded(box(spacing=10 if name == 'overview' else 14), 20)
            clamp = Adw.Clamp(maximum_size=1820 if name == 'overview' else 1100, tightening_threshold=1000)
            clamp.set_child(content)
            scroll.set_child(clamp)
            self.pages.add_titled(scroll, name, title)
            self.page_contents[name], self.page_scrolls[name] = content, scroll
        # Retain these names for the Overview and existing validation helpers.
        self.content, self.scroll = self.page_contents['overview'], self.page_scrolls['overview']
        self.build_health()
        self.build_controls()
        self.build_metrics()
        self.build_subsystems()
        self.build_findings_summary()
        self.sharing_test = SharingPanel(self.on_sharing_result)
        self.build_findings()
        reports = self.page_contents['reports']
        reports.append(label('Reports', 'title-2'))
        reports.append(label('Review and export the current observations. No diagnostic history is saved automatically.', 'dim-label', True))
        self.export = ExportPanel(self)
        reports.append(self.export)
        self.export.set_expanded(True)
        self.analysis = AnalysisPanel(self.copy_text, self.save_text, lambda: render_report(self.state.snapshot()))
        reports.append(self.analysis)
        for row in (self.analysis.choices, self.analysis.actions, self.sharing_test.actions):
            self.compact_row(row)
        self.build_report()
        self.preferences = PreferencesPanel(self)
        reports.append(self.preferences)
        self.refresh_dashboard()
        if getattr(application, 'autostart', True):
            self.mode.set_selected(0 if self.smoke_test else 1)
            GLib.idle_add(self.start_scan)
            self.live_timer = GLib.timeout_add_seconds(2, self.sample_live)
            GLib.idle_add(self.sample_once)
        if self.smoke_test:
            GLib.timeout_add_seconds(60, self.smoke_timeout)

    def show_page(self, name):
        self.pages.set_visible_child_name(name)

    def compact_row(self, row):
        # Adw activates one breakpoint at a time. Share the compact breakpoint
        # across rows, including the wider health-header breakpoint's setter.
        if not hasattr(self, 'compact_breakpoint'):
            self.compact_breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 700px'))
            self.compact_breakpoint.add_setter(self.health_row, 'orientation', Gtk.Orientation.VERTICAL)
            self.add_breakpoint(self.compact_breakpoint)
        self.compact_breakpoint.add_setter(row, 'orientation', Gtk.Orientation.VERTICAL)

    def build_health(self):
        hero = self.health_row = box(Gtk.Orientation.HORIZONTAL, 20)
        text = box(spacing=4)
        text.set_hexpand(True)
        self.health = label('Checking system health…', 'title-1', True)
        text.append(self.health)
        self.coverage = label('Current observations · local and read-only', 'dim-label', True)
        text.append(self.coverage)
        hero.append(text)
        self.counts = {}
        counts = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, column_spacing=8, row_spacing=6,
                             min_children_per_line=2, max_children_per_line=4, homogeneous=True)
        for status, name, index in ((Status.ERROR, 'Critical', 2), (Status.WARNING, 'Warnings', 3), (Status.INFO, 'Info', 4), (Status.UNAVAILABLE, 'Unavailable', 5)):
            button = Gtk.Button(label=f'0 {name}')
            button.add_css_class('indicator-' + status.value)
            button.connect('clicked', lambda _, i=index: self.filter_findings(i))
            counts.insert(button, -1)
            self.counts[status] = (button, name)
        hero.append(counts)
        self.content.append(hero)
        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 1050px'))
        breakpoint.add_setter(hero, 'orientation', Gtk.Orientation.VERTICAL)
        self.add_breakpoint(breakpoint)

    def build_controls(self):
        row = box(Gtk.Orientation.HORIZONTAL, 10)
        self.mode = Gtk.DropDown.new_from_strings(MODES)
        accessible_name(self.mode, 'Scan type')
        self.mode.set_hexpand(True)
        row.append(self.mode)
        self.scan_button = Gtk.Button(label='Run scan')
        self.scan_button.add_css_class('suggested-action')
        self.scan_button.connect('clicked', lambda _: self.start_scan())
        row.append(self.scan_button)
        self.cancel_button = Gtk.Button(label='Cancel', visible=False)
        self.cancel_button.connect('clicked', self.cancel_scan)
        row.append(self.cancel_button)
        active = self.get_application().settings.get('live_graphs')
        self.live_toggle = Gtk.ToggleButton(label='Live · 2s' if active else 'Paused', active=active)
        self.live_toggle.set_tooltip_text('Pause lightweight metrics; detailed scans never repeat automatically')
        self.live_toggle.connect('toggled', self.toggle_live)
        row.append(self.live_toggle)
        self.content.append(row)
        self.compact_row(row)
        progress = box(Gtk.Orientation.HORIZONTAL, 8)
        self.spinner = Gtk.Spinner(visible=False)
        progress.append(self.spinner)
        self.scan_status = label('Ready', 'dim-label', True)
        progress.append(self.scan_status)
        self.content.append(progress)

    def build_metrics(self):
        row = box(Gtk.Orientation.HORIZONTAL, 10)
        title = label('Live performance', 'heading')
        title.set_hexpand(True)
        row.append(title)
        self.live_status = label('Last 2 minutes · memory only', 'caption', True)
        row.append(self.live_status)
        self.content.append(row)

        # Keep the overview fast to scan: three primary system gauges and one
        # wider GPU surface. GPU temperature and VRAM remain live metrics, but
        # are presented inside the GPU surface instead of repetitive cards.
        gauges = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                             column_spacing=10, row_spacing=10,
                             min_children_per_line=1, max_children_per_line=3)
        self.metric_cards = {}
        for key in ('cpu', 'ram', 'cpu_temp'):
            card = GaugeCard(key, self.history, self.get_application().themes)
            card.set_paused(not self.live_toggle.get_active())
            gauges.insert(card, -1)
            self.metric_cards[key] = card
        self.content.append(gauges)

        self.gpu_card = GpuMetricCard(self.history, self.get_application().themes)
        self.gpu_card.set_paused(not self.live_toggle.get_active())
        self.content.append(self.gpu_card)
        # Preserve the metric-card mapping used by validation and extensions.
        self.metric_cards['gpu'] = self.gpu_card.utilization
        self.metric_cards['gpu_temp'] = self.gpu_card
        self.metric_cards['vram'] = self.gpu_card

    def build_subsystems(self):
        self.content.append(label('Subsystems', 'heading'))
        flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=False, column_spacing=10,
                           row_spacing=10, min_children_per_line=1, max_children_per_line=3)
        self.subsystems = {}
        for name, icon in zip(SUBSYSTEMS, ICONS):
            card = box(spacing=4)
            card.add_css_class('subsystem-card')
            card.add_css_class('overview-subsystem')
            card.set_size_request(250, -1)
            card.set_valign(Gtk.Align.START)
            heading = box(Gtk.Orientation.HORIZONTAL, 8)
            heading.append(Gtk.Image.new_from_icon_name(icon))
            heading.append(label(name, 'heading', True))
            card.append(heading)
            status = label('Not checked yet', 'dim-label', True)
            card.append(status)
            summary = label('', None, True)
            summary.set_max_width_chars(38)
            summary.set_lines(2)
            summary.set_ellipsize(Pango.EllipsizeMode.END)
            card.append(summary)
            inspect = Gtk.Button(label='View details →', halign=Gtk.Align.START)
            inspect.add_css_class('flat')
            accessible_name(inspect, name + ': View details')
            inspect.connect('clicked', lambda _, subsystem=name: self.filter_findings(1, subsystem))
            card.append(inspect)
            flow.insert(card, -1)
            self.subsystems[name] = (status, summary, inspect)
        self.content.append(flow)

    def build_findings_summary(self):
        self.overview_findings = box(spacing=8)
        self.overview_findings.add_css_class('subsystem-card')
        heading = box(Gtk.Orientation.HORIZONTAL, 8)
        title = label('Findings summary', 'heading', True)
        title.set_hexpand(True)
        heading.append(title)
        self.overview_findings.append(heading)
        self.summary_counts = label('', 'dim-label', True)
        self.overview_findings.append(self.summary_counts)
        self.preview_list = box(spacing=6)
        self.overview_findings.append(self.preview_list)
        self.view_findings = Gtk.Button(label='View all findings →', halign=Gtk.Align.START)
        self.view_findings.connect('clicked', lambda _: self.filter_findings(0))
        heading.append(self.view_findings)
        self.compact_row(heading)
        self.content.append(self.overview_findings)

    def build_findings(self):
        content = self.page_contents['findings']
        self.findings_anchor = label('Findings', 'title-2')
        content.append(self.findings_anchor)
        content.append(label('Attention shows Critical and Warnings. Every observation remains available in the filters.', 'dim-label', True))
        filters = box(Gtk.Orientation.HORIZONTAL, 10)
        self.severity = Gtk.DropDown.new_from_strings(SEVERITIES)
        self.scope = Gtk.DropDown.new_from_strings(('All subsystems', *SUBSYSTEMS))
        accessible_name(self.severity, 'Finding severity filter')
        accessible_name(self.scope, 'Subsystem filter')
        self.scope.set_hexpand(True)
        self.severity.connect('notify::selected', lambda *_: self.refresh_findings())
        self.scope.connect('notify::selected', lambda *_: self.refresh_findings())
        filters.append(self.severity)
        filters.append(self.scope)
        content.append(filters)
        self.compact_row(filters)
        self.finding_count = label('', 'dim-label', True)
        content.append(self.finding_count)
        content.append(self.sharing_test)
        self.finding_list = box(spacing=8)
        content.append(self.finding_list)

    def build_report(self):
        self.report = Gtk.Expander(label='Local dashboard report · unredacted')
        body, actions = box(), box(Gtk.Orientation.HORIZONTAL, 8)
        for title, callback in (('Copy report', lambda _: self.copy_text(render_report(self.state.snapshot()))),
                                ('Export report…', lambda _: self.open_export())):
            button = Gtk.Button(label=title)
            button.connect('clicked', callback)
            actions.append(button)
        body.append(actions)
        scroll, self.report_view = text_view()
        body.append(scroll)
        body.append(label('Current observations only. Findings retain their timestamps; graph history is never saved.', 'dim-label', True))
        set_expander_content(self.report, body)
        self.page_contents['reports'].append(self.report)

    def on_close(self, _):
        self.closed = True
        self.sharing_test.test.cancel()
        self.cancel.set()
        self.live_cancel.set()
        if self.live_timer:
            GLib.source_remove(self.live_timer)
            self.live_timer = None
        return False

    def on_sharing_result(self, check):
        self.state.manual_sharing = check
        self.refresh_dashboard()

    def show_preferences(self):
        self.preferences.set_expanded(True)
        self.scroll_to(self.preferences)

    def toggle_live(self, _):
        self.live_generation += 1
        self.live_cancel.set()
        self.live_cancel = threading.Event()
        active = self.live_toggle.get_active()
        self.get_application().settings.set('live_graphs', active)
        for card in {id(card): card for card in self.metric_cards.values()}.values():
            card.set_paused(not active)
        self.gpu_card.set_paused(not active)
        self.live_toggle.set_label('Live · 2s' if active else 'Paused')
        self.live_status.set_text('Resuming · memory only' if active else 'Paused · values frozen at last sample')

    def sample_once(self):
        self.sample_live()
        return False

    def sample_live(self):
        if self.closed:
            return False
        if self.live_busy or not self.live_toggle.get_active() or not self.get_mapped():
            return True
        self.live_busy = True
        generation, cancel = self.live_generation, self.live_cancel
        def worker():
            try:
                sample = self.sampler.sample(self.platform.create_runner(cancel), epoch=generation)
            except Exception as exc:
                logging.getLogger(__name__).error('Live sampling failed (%s)', type(exc).__name__)
                sample = None
            GLib.idle_add(self.on_sample, sample, generation)
        threading.Thread(target=worker, daemon=True, name='lucy-live').start()
        return True

    def on_sample(self, sample, generation):
        self.live_busy = False
        if self.closed or generation != self.live_generation or not self.live_toggle.get_active():
            return False
        if sample is None:
            self.live_status.set_text('Live sampling unavailable · retrying at next interval')
            return False
        self.history.append(sample)
        for key in ('cpu', 'ram', 'cpu_temp'):
            self.metric_cards[key].refresh(sample)
        self.gpu_card.refresh(sample)
        self.live_status.set_text(f'Updated {sample.observed_at:%H:%M:%S} · last 2 min · memory only')
        return False

    def cancel_scan(self, _):
        self.cancel.set()
        self.cancel_button.set_sensitive(False)
        self.scan_status.set_text('Cancelling detailed scan…')

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
        self.spinner.set_visible(True)
        self.spinner.start()
        self.scan_status.set_text(f'{mode} · collecting read-only observations…')
        def worker():
            try:
                result = scan(mode, self.platform.create_runner(self.cancel), lambda name, done, total: GLib.idle_add(self.on_progress, name, done, total), platform=self.platform)
                GLib.idle_add(self.on_finished, result)
            except Exception as exc:
                logging.getLogger(__name__).error('Scan failed (%s)', type(exc).__name__)
                GLib.idle_add(self.scan_failed)
        threading.Thread(target=worker, daemon=True, name='lucy-scan').start()
        return False

    def on_progress(self, name, done, total):
        if not self.closed:
            self.scan_status.set_text(f'{name} collected · {done}/{total} sections')
        return False

    def end_scan(self):
        self.scanning = False
        self.mode.set_sensitive(True)
        self.scan_button.set_sensitive(True)
        self.cancel_button.set_visible(False)
        self.spinner.stop()
        self.spinner.set_visible(False)

    def scan_failed(self):
        if not self.closed:
            self.end_scan()
            self.scan_status.set_text('Scan failed · previous observations retained with original timestamps')
        return False

    def on_finished(self, snapshot):
        if self.closed:
            return False
        self.end_scan()
        self.state.merge(snapshot)
        self.scan_status.set_text(f'{snapshot.mode} · {"Cancelled / partial" if snapshot.cancelled else "Completed"} · {snapshot.finished:%H:%M:%S %Z}')
        self.refresh_dashboard()
        if self.smoke_test:
            GLib.timeout_add_seconds(3, self.exercise_smoke)
        return False

    def refresh_dashboard(self):
        if hasattr(self, 'export'):
            self.export.invalidate()
        status, summary = self.state.status()
        counts = self.state.counts()
        # Health and coverage are separate concepts. Missing access should not
        # make an otherwise healthy machine look unhealthy.
        if counts[Status.ERROR.value]:
            headline, headline_status = 'Critical findings', Status.ERROR
        elif counts[Status.WARNING.value]:
            headline, headline_status = 'Needs attention', Status.WARNING
        elif self.state.latest:
            headline, headline_status = 'No problems detected', Status.OK
        else:
            headline, headline_status = 'Ready to scan', Status.INFO
        self.health.set_text(headline)
        for s in Status:
            self.health.remove_css_class('indicator-' + s.value)
        self.health.add_css_class('indicator-' + headline_status.value)
        for s, (button, name) in self.counts.items():
            button.set_label(f'{counts[s.value]} {name}')
        unavailable = counts[Status.UNAVAILABLE.value]
        if self.state.latest and unavailable:
            self.coverage.set_text(f'No detected faults · {unavailable} checks have limited or unavailable coverage')
        elif self.state.latest:
            self.coverage.set_text('Latest scan completed with full available coverage')
        else:
            self.coverage.set_text('Current observations · local and read-only')
        for subsystem, (status_label, summary_label, _) in self.subsystems.items():
            status, title = self.state.status(subsystem)
            status_label.set_text(title)
            status_label.remove_css_class('dim-label')
            for s in Status:
                status_label.remove_css_class('indicator-' + s.value)
            status_label.add_css_class('indicator-' + status.value)
            summary_label.set_text(self.state.subsystem_summary(subsystem))
        self.expanded_findings.intersection_update(finding_key(f) for f in self.state.findings())
        self.summary_counts.set_text(' · '.join(f'{counts[s.value]} {name}' for s, name in
                                    ((Status.ERROR, 'Critical'), (Status.WARNING, 'Warnings'),
                                     (Status.INFO, 'Info'), (Status.UNAVAILABLE, 'Unavailable'))))
        clear(self.preview_list)
        preview = self.state.attention_preview()
        if not preview:
            message = 'No immediate action required by current findings.' if self.state.latest else 'Run a scan to check system health.'
            self.preview_list.append(label(message, None, True))
        for finding in preview:
            row = label(f'{SEVERITY_LABEL[finding.check.status]}  {finding.check.title}',
                        'indicator-' + finding.check.status.value, True)
            row.set_lines(1)
            row.set_ellipsize(Pango.EllipsizeMode.END)
            self.preview_list.append(row)
        self.refresh_findings()
        self.report_view.get_buffer().set_text(render_report(self.state.snapshot()))

    def subsystem_summary(self, name):
        return self.state.subsystem_summary(name)

    def filter_findings(self, severity, subsystem=None):
        self.severity.set_selected(severity)
        self.scope.set_selected(SUBSYSTEMS.index(subsystem) + 1 if subsystem else 0)
        self.show_page('findings')
        self.scroll_to(self.findings_anchor)

    def refresh_findings(self):
        if not hasattr(self, 'finding_list'):
            return
        clear(self.finding_list)
        scope = self.scope.get_selected()
        subsystem = SUBSYSTEMS[scope - 1] if scope else None
        items = self.state.findings(subsystem)
        visible = self.state.filtered_findings(self.severity.get_selected(), subsystem)
        self.sharing_test.set_visible(subsystem == 'Discord / Screen Sharing')
        self.finding_count.set_text(f'{len(visible)} of {len(items)} checks shown · {len(self.state.findings())} total')
        if not visible:
            message = ('No findings currently require attention.' if self.severity.get_selected() == 0 else 'No findings in this filter.')
            if not self.state.latest:
                message = 'Run a scan from Overview to populate findings.'
            self.finding_list.append(label(message, 'dim-label', True))
            if self.severity.get_selected() == 0:
                for title, severity in (('Show informational findings', 4), ('Show unavailable checks', 5)):
                    button = Gtk.Button(label=title, halign=Gtk.Align.START)
                    button.connect('clicked', lambda _, value=severity: self.severity.set_selected(value))
                    self.finding_list.append(button)
        for finding in visible:
            self.finding_list.append(self.finding_row(finding))

    def finding_row(self, finding):
        check = finding.check
        row = box(spacing=8)
        row.add_css_class('finding-row')
        row.add_css_class('severity-' + check.status.value)
        heading = box(Gtk.Orientation.HORIZONTAL, 12)
        heading.append(label(SEVERITY_LABEL[check.status], 'indicator-' + check.status.value))
        title = label(check.title, 'heading', True)
        title.set_hexpand(True)
        heading.append(title)
        row.append(heading)
        row.append(label(check.summary, None, True))
        row.append(label(finding.explanation, 'dim-label', True))
        stamp = check.observed_at.isoformat(timespec='seconds') if check.observed_at else 'Unknown'
        row.append(label(f'{finding.subsystem} · {check.support.value} · {check.source} · {stamp}', 'caption', True))
        actions = box(Gtk.Orientation.HORIZONTAL, 8)
        self.compact_row(actions)
        copy = Gtk.Button(label='Copy')
        copy.connect('clicked', lambda _: self.copy_text(finding.text))
        actions.append(copy)
        key = finding_key(finding)
        detail = Gtk.ToggleButton(label='Details', active=key in self.expanded_findings)
        accessible_name(detail, check.title + ': Details')
        actions.append(detail)
        ai = Gtk.Button(label='Explain with AI')
        ai.connect('clicked', lambda _: self.open_analysis(finding))
        actions.append(ai)
        row.append(actions)
        evidence = Gtk.Revealer(reveal_child=key in self.expanded_findings)
        body = box(spacing=6)
        body.append(label('What happened: ' + check.summary, None, True))
        body.append(label('Why it matters: ' + finding.explanation, None, True))
        body.append(label('Evidence', 'caption-heading'))
        scroll, _ = text_view(check.details or check.summary, height=140)
        body.append(scroll)
        if finding.guidance:
            body.append(label(guidance_text(finding.guidance), None, True))
        body.append(label(f'Source: {check.source} · Timestamp: {stamp}', 'caption', True))
        evidence.set_child(body)
        row.append(evidence)
        def toggle_details(button):
            expanded = button.get_active()
            evidence.set_reveal_child(expanded)
            (self.expanded_findings.add if expanded else self.expanded_findings.discard)(key)
        detail.connect('toggled', toggle_details)
        return row

    def open_analysis(self, finding=None):
        text = finding.text if finding else render_report(self.state.snapshot())
        title = 'Finding: ' + finding.check.title if finding else 'Current dashboard report · original observation timestamps retained'
        self.analysis.prepare(text, title)
        self.scroll_to(self.analysis)

    def open_export(self):
        self.export.privacy.set_selected(0 if self.get_application().settings.get('report_privacy') == 'sanitized' else 1)
        self.export.set_expanded(True)
        self.export.build_preview()
        self.scroll_to(self.export)

    def scroll_to(self, widget):
        target = next(((name, content) for name, content in self.page_contents.items()
                       if widget == content or widget.is_ancestor(content)), None)
        if target is None:
            return
        name, content = target
        self.show_page(name)
        def scroll():
            if not self.closed and self.pages.get_visible_child_name() == name:
                ok, bounds = widget.compute_bounds(content)
                if ok:
                    adjustment = self.page_scrolls[name].get_vadjustment()
                    adjustment.set_value(max(0, min(bounds.get_y() + content.get_margin_top(),
                                                    adjustment.get_upper() - adjustment.get_page_size())))
            return False
        GLib.timeout_add(80, scroll)

    def copy_text(self, text):
        self.get_clipboard().set(text)
        self.toast_overlay.add_toast(Adw.Toast(title='Copied to clipboard'))

    def show_about(self):
        from ..runtime import render_build_info
        dialog = Adw.AlertDialog(heading=DISPLAY_NAME, body=f'{TAGLINE}\n{PUBLISHER}\n\n' + render_build_info(platform_name=self.platform.name))
        dialog.add_response('close', 'Close')
        dialog.present(self)
        return dialog

    def save_text(self, text, name):
        from .file_save import ReportSaver
        return ReportSaver(self, lambda message: self.toast_overlay.add_toast(Adw.Toast(title=message))).choose(text, name)

    def exercise_smoke(self):
        try:
            assert len(self.history.samples) >= 2, 'Not enough live samples reached GTK'
            self.filter_findings(1)
            assert self.state.findings()
            self.open_analysis(self.state.findings()[0])
            assert not self.analysis.copy_prompt.get_sensitive()
            self.analysis.confirm.set_active(True)
            assert self.analysis.copy_prompt.get_sensitive()
            self.analysis.provider.set_selected(1)
            assert not self.analysis.confirm.get_active()
            assert not self.analysis.copy_prompt.get_sensitive()
            self.analysis.prepare('/home/alice/private 192.168.1.2', 'Synthetic privacy regression')
            buffer = self.analysis.preview.get_buffer()
            preview = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            assert '/home/alice' not in preview and '192.168.1.2' not in preview
            self.analysis.confirm.set_active(True)
            self.analysis.prepare('A different finding', 'New finding')
            assert not self.analysis.confirm.get_active()
            self.live_toggle.set_active(False)
            assert self.live_toggle.get_label() == 'Paused'
            assert len(self.get_application().get_windows()) == 1
            from ..themes.catalog import THEMES
            app = self.get_application()
            for theme in THEMES:
                app.themes.select(theme, persist=False)
                assert self.preferences.theme_button.get_label() == THEMES[theme].name
                assert self.preferences.theme_choices[theme].get_active()
                for card in self.metric_cards.values():
                    assert card.themes.current == theme
                    assert 'PAUSED' in card.state_label.get_text()
            app.themes.select('system', persist=False)
            assert app.get_style_manager().get_color_scheme() == Adw.ColorScheme.DEFAULT
            assert not self.sharing_test.test.active and self.sharing_test.test.result is None
            self.sharing_test.consent.set_active(True)
            self.sharing_test.begin(None)
            self.sharing_test.finish('INCONCLUSIVE')
            assert not self.sharing_test.consent.get_active()
            assert not self.sharing_test.start.get_sensitive()
            self.export.set_expanded(True)
            self.export.build_preview()
            assert not self.export.save.get_sensitive()
            self.analysis.set_expanded(False)
            self.set_default_size(720, 760)
            GLib.timeout_add_seconds(1, self.smoke_finish)
        except Exception:
            logging.getLogger(__name__).exception('Dashboard UI smoke failed')
            self.close()
        return False

    def smoke_finish(self):
        if not self.export.prepared or not self.export.save.get_sensitive():
            logging.getLogger(__name__).error('GTK smoke failed: export preview did not complete')
            self.close()
            return False
        self.export.format.set_selected(1)
        assert not self.export.save.get_sensitive(), 'Changed format must invalidate export consent'
        print('GTK smoke passed: unified dashboard, live samples, 13 runtime themes, preferences, export preview, manual sharing cancellation, fresh AI consent, one application window.')
        self.get_application().smoke_passed = True
        self.close()
        return False

    def smoke_timeout(self):
        if not self.closed:
            print('GTK smoke test timed out', flush=True)
            self.close()
        return False
