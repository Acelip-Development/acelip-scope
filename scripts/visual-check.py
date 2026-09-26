"""Explicit GTK visual QA. Screenshots contain synthetic data, never host diagnostics.

Run with the distribution Python from an accessible desktop session.
Writes only project var/v14-* artifacts. Never opens a screen-capture portal.
"""
import os
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
os.environ['GSETTINGS_BACKEND'] = 'memory'
os.environ['GSK_RENDERER'] = 'cairo'
os.environ['XDG_CACHE_HOME'] = str(PROJECT / 'var/cache')

from datetime import datetime, timedelta
import json
import math
from lucy_diagnose.ui.application import LucyApplication, Gtk
from gi.repository import GLib
from lucy_diagnose.models import Check, Snapshot, Status
from lucy_diagnose.telemetry import Sample
from lucy_diagnose.themes.catalog import THEMES

app = LucyApplication(smoke_test=True)
app.smoke_test = False
app.autostart = False
app.preferences_path = PROJECT / 'var/v14-visual-preferences.json'
passed = False
css_errors = []
steps = []


def capture(name):
    window = app.get_active_window()
    paintable = Gtk.WidgetPaintable.new(window)
    snap = Gtk.Snapshot.new()
    paintable.snapshot(snap, window.get_width(), window.get_height())
    texture = window.get_renderer().render_texture(snap.to_node(), None)
    texture.save_to_png(str(PROJECT / 'var' / (name + '.png')))
    assert not css_errors, css_errors
    assert len(app.get_windows()) == 1
    print(name, window.get_width(), window.get_height(), flush=True)


def capture_selector():
    window = app.get_active_window()
    widget = window.preferences.popover
    assert widget.get_mapped(), 'Theme selector was not displayed'
    assert len(window.preferences.theme_choices) == 13
    paintable = Gtk.WidgetPaintable.new(widget)
    snap = Gtk.Snapshot.new()
    paintable.snapshot(snap, widget.get_width(), widget.get_height())
    texture = widget.get_native().get_renderer().render_texture(snap.to_node(), None)
    texture.save_to_png(str(PROJECT / 'var/v14-theme-selector.png'))


def advance():
    global passed
    try:
        if steps:
            steps.pop(0)()
            GLib.timeout_add(650, advance)
        else:
            passed = True
            app.get_active_window().close()
            app.quit()
    except Exception:
        import traceback
        traceback.print_exc()
        app.quit()
    return False


def setup():
    window = app.get_active_window()
    window.unmaximize()
    window.set_default_size(1920, 1000)
    window.window_title.set_subtitle('SAMPLE DATA · visual QA · no host diagnostics')
    window.live_toggle.set_active(True)
    app.themes.backend.provider.connect('parsing-error', lambda _, section, error: css_errors.append(str(error)))
    now = datetime.now().astimezone()
    sections = {
        'Overview': [Check('Operating system', 'Sample Linux distribution'), Check('CPU model', 'AMD Ryzen sample workstation'),
                     Check('GPU', 'NVIDIA GeForce RTX 4070 Ti', Status.OK), Check('NVIDIA driver', 'Sample driver'),
                     Check('Disk · /', '68% · 308 GiB / 456 GiB', Status.OK)],
        'Health': [Check('Failed services / units', '1 failed unit', Status.ERROR, 'example.service loaded failed failed Sample service', count=1),
                   Check('Recent journal errors', '3 visible entries · 24 hours ago', Status.WARNING, 'Synthetic journal evidence.', count=3)],
        'Storage': [Check('Disk · /', '68% · 308 GiB / 456 GiB', Status.OK),
                    Check('SMART · /dev/nvme0n1', 'Permission denied · not elevated', Status.UNAVAILABLE, 'Sample permission restriction.')],
        'Network': [Check('Internet reachability', 'ICMP reply received', Status.OK), Check('Gateway reachability', 'ICMP reply received', Status.OK)],
        'AI Stack': [Check('Ollama service', 'active · running', Status.OK), Check('Ollama API', 'Available · sample version', Status.OK), Check('Codex', 'sample version')],
        'Discord / Screen Sharing': [Check('ScreenCast portal', 'No source types advertised', Status.WARNING),
                                    Check('Discord process', 'Discord'), Check('Discord deb', 'Sample version'),
                                    Check('PipeWire socket', 'Socket exists; not connected by LUCY'),
                                    Check('Screen-sharing verification', 'End-to-end sharing unverified')],
    }
    window.on_finished(Snapshot('Full Scan', now, sections, now))
    for i in range(60):
        values = {'cpu': 22 + 12 * math.sin(i / 6), 'cpu_temp': 52 + 5 * math.sin(i / 10), 'ram': 31 + i / 60,
                  'gpu': 12 + 8 * math.sin(i / 3), 'gpu_temp': 48 + 3 * math.sin(i / 8), 'vram': 18 + 4 * math.sin(i / 12)}
        sample = Sample(now - timedelta(seconds=(59 - i) * 2), values,
                       {'cpu': 'Across all logical CPUs', 'cpu_temp': 'Primary CPU sensor · k10temp / Tctl', 'ram': '19.8 GiB / 62.4 GiB',
                        'gpu': 'NVIDIA GPU 1', 'gpu_temp': 'NVIDIA GPU 1 sensor', 'vram': '2300 / 12282 MiB'})
        window.on_sample(sample, window.live_generation)
    for key in THEMES:
        steps.append(lambda key=key: app.themes.select(key, persist=False))
        steps.append(lambda key=key: capture('v14-' + key + '-dashboard'))
    steps.extend([lambda: app.themes.select('system', persist=False), window.show_preferences, lambda: window.preferences.theme_button.popup(),
                  capture_selector, lambda: capture('v14-theme-settings'), window.preferences.theme_button.popdown,
                  lambda: window.preferences.set_expanded(False), sharing, lambda: capture('v14-screen-sharing'),
                  cancel_sharing, expand_card, lambda: capture('v14-expanded-card'), export_json,
                  check_export, lambda: capture('v14-export-preview'), show_details, lambda: capture('v14-guidance'),
                  compact, lambda: capture('v14-compact')])
    GLib.timeout_add(650, advance)
    return False


def sharing():
    window = app.get_active_window()
    app.themes.select('system', persist=False)
    window.sharing_test.set_expanded(True)
    window.sharing_test.consent.set_active(True)
    window.sharing_test.begin(None)
    window.scroll_to(window.sharing_test)


def cancel_sharing():
    window = app.get_active_window()
    window.sharing_test.finish('INCONCLUSIVE')
    assert not window.sharing_test.start.get_sensitive()
    assert not window.sharing_test.test.active
    window.sharing_test.set_expanded(False)


def expand_card():
    window = app.get_active_window()
    window.subsystems['Discord / Screen Sharing'][2].set_expanded(True)
    window.scroll_to(window.subsystems['Discord / Screen Sharing'][2])


def export_json():
    window = app.get_active_window()
    window.export.format.set_selected(1)
    window.open_export()


def check_export():
    window = app.get_active_window()
    assert window.export.prepared and window.export.save.get_sensitive()
    data = json.loads(window.export.prepared[0])
    assert data['app']['version'] == '1.4.0-dev'
    assert data['privacy'] == 'sanitized'
    # Exercise the Save action without opening an unattended file picker or writing a report.
    observed = []
    original = window.save_text
    window.save_text = lambda *args: observed.append(args)
    window.export.save.emit('clicked')
    window.save_text = original
    assert observed == [window.export.prepared]


def show_details():
    window = app.get_active_window()
    window.export.set_expanded(False)
    window.filter_findings(2)
    row = window.finding_list.get_first_child()
    child = row.get_first_child()
    while child:
        if isinstance(child, Gtk.Revealer):
            child.set_reveal_child(True)
        child = child.get_next_sibling()
    window.scroll_to(window.findings_anchor)


def compact():
    window = app.get_active_window()
    app.themes.select('arcanum', persist=False)
    window.live_toggle.set_active(False)
    window.unmaximize()
    window.set_default_size(720, 800)
    for _, _, expander, _ in window.subsystems.values():
        expander.set_expanded(False)
    window.scroll.get_vadjustment().set_value(0)


app.connect_after('activate', lambda _: GLib.timeout_add(250, setup))
GLib.timeout_add_seconds(55, lambda: app.quit())
app.run(['lucy-visual-check'])
raise SystemExit(0 if passed else 1)
