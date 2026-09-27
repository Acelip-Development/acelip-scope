"""Real GTK integration; run explicitly with a display, never during headless unit discovery.

Uses labeled synthetic observations and isolated preferences; no scans, capture
portal or clipboard writes. RC2_QA_OUTPUT optionally saves app-widget screenshots.
"""
import os
import itertools
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from lucy_diagnose.ui.application import LucyApplication, Gtk, Gdk
from gi.repository import GLib
from lucy_diagnose.dashboard import finding_key
from lucy_diagnose.models import Status
from lucy_diagnose.settings import SettingsStore
from lucy_diagnose.telemetry import Sample
from lucy_diagnose.themes.catalog import THEMES
from tests.test_dashboard import NOW, snapshot
from tests.test_dashboard_rc2 import sample_state


def widgets(root):
    yield root
    child = root.get_first_child()
    while child:
        yield from widgets(child)
        child = child.get_next_sibling()


def settle(seconds=.12):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        time.sleep(.005)


def text(root):
    return '\n'.join(w.get_text() for w in widgets(root) if isinstance(w, Gtk.Label))


def click(root, title):
    button = next(w for w in widgets(root) if isinstance(w, Gtk.Button) and w.get_label() == title)
    button.emit('clicked')
    settle()
    return button


@unittest.skipUnless(Gdk.Display.get_default(), 'Requires a real GTK display; run the explicit UI suite')
class RC2NavigationTests(unittest.TestCase):
    application_ids = itertools.count()
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = LucyApplication(smoke_test=True)  # NON_UNIQUE; never activates installed RC1.
        self.app.set_application_id('io.github.acelip_development.ScopeUITest' + str(next(self.application_ids)))
        self.app.smoke_test = False
        self.app.autostart = False
        self.app.preferences_path = Path(self.temp.name)/'preferences.json'
        self.app.register(None)
        self.app.activate()
        self.w = self.app.get_active_window()
        self.w.window_title.set_subtitle('SAMPLE DATA · RC2 UI validation')
        self.w.state = sample_state()
        self.w.refresh_dashboard()
        self.w.on_sample(Sample(NOW, {'cpu': 5.5, 'cpu_temp': 51, 'ram': 31, 'gpu': None,
                                     'gpu_temp': None, 'vram': None}, {'cpu_temp': 'k10temp / Tctl · SAMPLE'}), self.w.live_generation)
        self.w.set_default_size(1366, 1000)
        self.css_errors = []
        self.app.themes.backend.provider.connect('parsing-error', lambda _, section, error: self.css_errors.append(str(error)))
        settle()

    def tearDown(self):
        self.w.close()
        Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(), self.app.themes.backend.provider)
        self.app.settings.close()
        self.app.quit()
        settle(.05)
        self.temp.cleanup()

    def capture(self, filename=None):
        settle()
        snap = Gtk.Snapshot.new()
        Gtk.WidgetPaintable.new(self.w).snapshot(snap, self.w.get_width(), self.w.get_height())
        node = snap.to_node()
        self.assertIsNotNone(node)
        texture = self.w.get_renderer().render_texture(node, None)
        self.assertGreater(texture.get_width(), 0)
        self.assertFalse(self.css_errors)
        if filename and os.environ.get('RC2_QA_OUTPUT'):
            output = Path(os.environ['RC2_QA_OUTPUT'])/filename
            output.parent.mkdir(parents=True, exist_ok=True)
            self.assertTrue(texture.save_to_png(str(output)))

    def test_overview_bounded_preview_and_counter_navigation(self):
        self.assertFalse(self.w.finding_list.is_ancestor(self.w.content))
        self.assertFalse(self.w.export.is_ancestor(self.w.content))
        self.assertFalse(self.w.sharing_test.is_ancestor(self.w.content))
        preview = list(widgets(self.w.preview_list))
        self.assertEqual(sum(isinstance(w, Gtk.Label) for w in preview), 3)
        self.assertNotIn('example.service', text(self.w.content))
        self.assertIn('1 Critical · 3 Warnings · 4 Info · 2 Unavailable', self.w.summary_counts.get_text())
        self.capture('rc2-overview.png')
        self.w.counts[Status.INFO][0].emit('clicked')
        self.assertEqual(self.w.pages.get_visible_child_name(), 'findings')
        self.assertEqual(self.w.severity.get_selected(), 4)
        self.assertIn('4 of 10 checks', self.w.finding_count.get_text())

    def test_view_all_starts_with_attention_and_empty_state_links_work(self):
        self.w.view_findings.emit('clicked')
        self.assertEqual(self.w.pages.get_visible_child_name(), 'findings')
        self.assertEqual(self.w.severity.get_selected(), 0)
        self.assertIn('4 of 10 checks', self.w.finding_count.get_text())
        self.capture('rc2-findings-actionable.png')
        self.w.state.groups = {g:[c for c in checks if c.status not in {Status.ERROR, Status.WARNING}]
                               for g, checks in self.w.state.groups.items()}
        self.w.refresh_dashboard()
        self.assertIn('No findings currently require attention.', text(self.w.finding_list))
        self.capture('rc2-findings-empty.png')
        click(self.w.finding_list, 'Show informational findings')
        self.assertEqual(self.w.severity.get_selected(), 4)
        self.w.severity.set_selected(0)
        click(self.w.finding_list, 'Show unavailable checks')
        self.assertEqual(self.w.severity.get_selected(), 5)
        self.assertIn('2 of 6 checks', self.w.finding_count.get_text())
        self.w.severity.set_selected(1)
        self.assertIn('6 of 6 checks', self.w.finding_count.get_text())

    def test_navigation_and_filters_preserve_state_live_history_and_expansion(self):
        before = self.w.state.snapshot().to_dict()
        latest = self.w.state.latest
        self.w.filter_findings(1)
        self.capture('rc2-findings-all.png')
        first = self.w.finding_list.get_first_child()
        click(first, 'Details')
        key = finding_key(self.w.state.findings()[0])
        self.assertIn(key, self.w.expanded_findings)
        history = self.w.history
        with patch.object(self.w, 'start_scan', side_effect=AssertionError('Navigation must not scan')):
            for page in ('reports', 'overview', 'findings'):
                self.w.show_page(page)
                settle()
            self.assertIs(self.w.finding_list.get_first_child(), first)
            self.w.severity.set_selected(4)
            self.w.severity.set_selected(1)
        details = next(w for w in widgets(self.w.finding_list.get_first_child()) if isinstance(w, Gtk.ToggleButton))
        self.assertTrue(details.get_active())
        self.assertEqual(self.w.state.snapshot().to_dict(), before)
        self.assertIs(self.w.state.latest, latest)
        self.assertIs(self.w.history, history)
        self.w.on_sample(Sample(NOW, {'cpu': 6, 'cpu_temp': 50, 'ram': 30, 'gpu': None,'gpu_temp': None,'vram': None}, {'cpu_temp':'k10temp / Tctl'}), self.w.live_generation)
        self.assertEqual(len(history.samples), 2)
        self.assertIn('k10temp / Tctl', self.w.metric_cards['cpu_temp'].note.get_text())

    def test_subsystem_details_sharing_cancellation_and_copy_keep_evidence(self):
        self.w.subsystems['System'][2].emit('clicked')
        self.assertEqual(self.w.pages.get_visible_child_name(), 'findings')
        self.assertIn('4 of 4 checks', self.w.finding_count.get_text())
        cooling = next(f for f in self.w.state.findings('System') if f.check.title == 'Cooling telemetry')
        rows = [w for w in widgets(self.w.finding_list) if w.has_css_class('finding-row')]
        row = next(r for r in rows if 'Cooling telemetry' in text(r))
        click(row, 'Details')
        with patch.object(self.w, 'copy_text') as copied:
            click(row, 'Copy')
            self.assertEqual(copied.call_args.args[0], cooling.text)
            self.assertIn('Pump: 2100 RPM', copied.call_args.args[0])
        self.capture('rc2-subsystem-details.png')
        self.w.subsystems['Discord / Screen Sharing'][2].emit('clicked')
        self.assertTrue(self.w.sharing_test.get_visible())
        self.assertFalse(self.w.sharing_test.start.get_sensitive())
        self.w.sharing_test.set_expanded(True)
        self.w.sharing_test.consent.set_active(True)
        self.w.sharing_test.start.emit('clicked')
        self.assertTrue(self.w.sharing_test.test.active)
        click(self.w.sharing_test, 'Cancel test')
        self.assertFalse(self.w.sharing_test.test.active)
        self.assertFalse(self.w.sharing_test.consent.get_active())
        self.w.filter_findings(1, 'Network')
        self.assertFalse(self.w.sharing_test.get_visible())

    def test_reports_export_privacy_and_ai_fresh_consent(self):
        self.w.open_export()
        deadline=time.monotonic()+10
        while self.w.export.busy and time.monotonic()<deadline: settle(.02)
        self.assertEqual(self.w.pages.get_visible_child_name(), 'reports')
        self.assertTrue(self.w.export.save.get_sensitive())
        with patch.object(self.w, 'save_text') as saved:
            self.w.export.save.emit('clicked')
            self.assertEqual(saved.call_args.args, self.w.export.prepared)
        self.w.export.format.set_selected(1)
        self.assertFalse(self.w.export.save.get_sensitive())
        self.w.export.build_preview()
        while self.w.export.busy and time.monotonic()<deadline: settle(.02)
        self.assertTrue(self.w.export.prepared[1].endswith('.json'))
        self.w.open_analysis(self.w.state.findings()[0])
        self.assertFalse(self.w.analysis.copy_prompt.get_sensitive())
        self.w.analysis.confirm.set_active(True)
        self.assertTrue(self.w.analysis.copy_prompt.get_sensitive())
        self.w.open_analysis(self.w.state.findings()[1])
        self.assertFalse(self.w.analysis.confirm.get_active())

    def test_themes_render_all_views_and_persist_without_resetting_navigation(self):
        self.assertEqual(self.app.themes.current, 'system')
        for theme in THEMES:
            self.app.themes.select(theme)
            for page in ('overview', 'findings', 'reports'):
                self.w.show_page(page)
                self.capture(f'rc2-themes/{theme}-{page}.png')
                self.assertEqual(self.w.pages.get_visible_child_name(), page)
                self.assertTrue(all(c.themes.current == theme for c in self.w.metric_cards.values()))
        self.app.settings.close()
        restored=SettingsStore(self.app.preferences_path)
        self.assertEqual(restored.get('theme'), list(THEMES)[-1])
        restored.close()

    def test_keyboard_switcher_filters_details_and_visible_focus(self):
        self.w.navigation.get_first_child().grab_focus()
        focused=set()
        for _ in range(30):
            focus=self.w.get_focus()
            if focus: focused.add(type(focus).__name__)
            self.w.emit('move-focus', Gtk.DirectionType.TAB_FORWARD)
            settle(.01)
        self.assertGreaterEqual(len(focused), 3)
        tabs=[w for w in widgets(self.w.navigation) if isinstance(w,Gtk.ToggleButton)]
        self.assertEqual(len(tabs), 3)
        for button,name in zip(tabs,('overview','findings','reports')):
            button.grab_focus()
            self.assertTrue(button.activate())  # Keyboard activation path, not page setter.
            settle(.3)
            self.assertEqual(self.w.pages.get_visible_child_name(),name)
        self.w.filter_findings(0)
        self.w.severity.grab_focus()
        self.assertIsNotNone(self.w.get_focus())
        self.assertIn('CRITICAL', text(self.w.finding_list).upper())
        self.assertEqual(self.w.severity.get_accessible_role(), Gtk.AccessibleRole.COMBO_BOX)
        self.capture('rc2-keyboard-focus.png')

    def test_responsive_all_pages_at_desktop_compact_and_150_percent(self):
        settings=Gtk.Settings.get_default(); dpi=settings.get_property('gtk-xft-dpi')
        try:
            for width,height,scale in ((1740,1000,1),(1366,900,1),(600,900,1),(480,900,1),(600,1000,1.5),(480,1000,1.5)):
                settings.set_property('gtk-xft-dpi',int(96*scale*1024))
                self.w.set_default_size(width,height)
                self.w.set_focus(None)
                for page in ('overview','findings','reports'):
                    self.w.show_page(page)
                    settle(.3)
                    self.assertLessEqual(self.w.get_width(),width, (page,width,scale,'window forced wider'))
                    content=self.w.page_contents[page]
                    self.assertLessEqual(content.get_width(),self.w.get_width(), (page,width,scale,'content overflow'))
                    self.assertLessEqual(content.measure(Gtk.Orientation.HORIZONTAL,-1)[0],self.w.get_width(), (page,width,scale,'minimum width overflow'))
                    nav=self.w.navigation
                    self.assertLessEqual(nav.get_width(),self.w.get_width())
                    filename=f'rc2-layout-{width}-{scale}-{page}.png'
                    if width==600 and scale==1 and page=='overview': filename='rc2-compact.png'
                    self.capture(filename)
            # Expanded controls must reflow too; collapsed panels must not hide
            # minimum-width problems in AI consent, sharing consent or Preferences.
            for page in ('reports', 'findings'):
                self.w.show_page(page)
                if page == 'reports':
                    self.w.analysis.set_expanded(True)
                    self.w.preferences.set_expanded(True)
                else:
                    self.w.filter_findings(1, 'Discord / Screen Sharing')
                    self.w.sharing_test.set_expanded(True)
                settle(.3)
                content=self.w.page_contents[page]
                self.assertLessEqual(content.get_width(),self.w.get_width(), (page,'expanded overflow'))
                self.assertLessEqual(content.measure(Gtk.Orientation.HORIZONTAL,-1)[0],self.w.get_width(), (page,'expanded minimum width'))
                self.capture(f'rc2-expanded-150-{page}.png')
        finally:
            self.w.set_focus(None)
            settings.set_property('gtk-xft-dpi',dpi)
