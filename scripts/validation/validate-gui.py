"""Exercise actual GTK controls/scans with isolated QA preferences and screenshots.

No capture portal, system settings, clipboard or AI handoff is used. Screenshots
render only the app widget tree. Exports use the real preview/Save callback, with
the native file-picker boundary replaced by an explicit QA output destination.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--label', required=True)
args = parser.parse_args()
if not args.label.replace('-', '').isalnum():
    parser.error('label must contain only letters, digits or hyphens')
os.environ['GSETTINGS_BACKEND'] = 'memory'
os.environ['GSK_RENDERER'] = 'cairo'
os.environ['XDG_CACHE_HOME'] = str(PROJECT / 'var/cache')
from lucy_diagnose.ui.application import LucyApplication, Gtk
from gi.repository import GLib, Adw
from lucy_diagnose.scanner import MODES
from lucy_diagnose.themes.catalog import THEMES
from lucy_diagnose.settings import SettingsStore
from lucy_diagnose import __version__

(PROJECT / 'var').mkdir(exist_ok=True)
qa = tempfile.TemporaryDirectory(prefix='v14-gui-', dir=PROJECT / 'var')
app = LucyApplication(smoke_test=True)
app.smoke_test = False
app.autostart = False
app.preferences_path = Path(qa.name) / 'preferences.json'
record = {'version': __version__, 'label': args.label, 'scans': {}, 'themes': {},
          'screenshots': [], 'capture': 'NOT TESTED; app widget rendering only',
          'file_picker': 'NOT TESTED; Save callback writes to explicit QA destination'}
phase = 'init'
current = None
queue = list(MODES)
errors = []
passed = False
started = time.monotonic()


def capture(window, suffix):
    paintable = Gtk.WidgetPaintable.new(window)
    snap = Gtk.Snapshot.new()
    paintable.snapshot(snap, window.get_width(), window.get_height())
    texture = window.get_renderer().render_texture(snap.to_node(), None)
    name = f'v14-{args.label}{suffix}.png'
    assert texture.save_to_png(str(PROJECT / 'var' / name))
    record['screenshots'].append({'path': name, 'width': window.get_width(), 'height': window.get_height()})


def tick():
    global phase, current, passed
    try:
        if time.monotonic() - started > 180:
            raise TimeoutError('GUI acceptance deadline')
        w = app.get_active_window()
        assert w is not None
        if phase == 'init':
            assert app.themes.current == 'system'
            record['first_launch_system'] = 'PASS'
            app.themes.backend.provider.connect('parsing-error', lambda _, section, error: errors.append(str(error)))
            w.set_default_size(1920, 1000)
            w.live_timer = GLib.timeout_add(400, w.sample_live)
            phase = 'scans'
        elif phase == 'scans':
            if w.scanning:
                return True
            if current:
                assert w.state.latest.mode == current and not w.state.latest.cancelled
                assert not any(f.check.summary.startswith('Collector failed') for f in w.state.findings())
                record['scans'][current] = 'PASS'
                print('GTK scan', current, flush=True)
                current = None
            if queue:
                current = queue.pop(0)
                w.mode.set_selected(MODES.index(current))
                w.start_scan()
            else:
                assert len(w.history.samples) >= 2
                w.mode.set_selected(MODES.index('Full Scan'))
                w.start_scan()
                w.cancel_scan(None)
                phase = 'cancel'
        elif phase == 'cancel':
            if w.scanning:
                return True
            assert w.state.latest.cancelled
            record['scan_cancellation'] = 'PASS'
            w.start_scan()
            phase = 'restore'
        elif phase == 'restore':
            if w.scanning:
                return True
            assert not w.state.latest.cancelled
            w.live_toggle.set_active(False)
            record['paused_samples'] = len(w.history.samples)
            phase = 'pause'
        elif phase == 'pause':
            assert len(w.history.samples) == record['paused_samples']
            assert w.live_toggle.get_label() == 'Paused'
            w.live_toggle.set_active(True)
            phase = 'resume'
        elif phase == 'resume':
            if len(w.history.samples) < record['paused_samples'] + 2:
                return True
            record['live_graphs_pause_resume'] = 'PASS'
            record['metric_availability'] = {key: value is not None for key, value in w.history.samples[-1].values.items()}
            for key in THEMES:
                app.themes.select(key)
                app.settings.flush()
                restored = SettingsStore(app.preferences_path)
                assert restored.get('theme') == key
                restored.close()
                assert w.preferences.theme_choices[key].get_active()
                record['themes'][key] = 'PASS: selected and reloaded from QA preferences'
            app.themes.select('system')
            assert app.get_style_manager().get_color_scheme() == Adw.ColorScheme.DEFAULT
            record['system_appearance'] = {'dark': app.get_style_manager().get_dark(),
                                         'host_preference_available': app.get_style_manager().get_system_supports_color_schemes()}
            w.exercise_smoke()  # existing real UI assertions: privacy, consent, manual sharing cancellation
            # setup() replaces its scheduled completion; this harness owns exit.
            phase = 'markdown'
        elif phase == 'markdown':
            if w.export.busy:
                return True
            w.export.format.set_selected(0)
            w.export.build_preview()
            phase = 'save-markdown'
        elif phase in {'save-markdown', 'save-json'}:
            if w.export.busy:
                return True
            assert w.export.prepared and w.export.save.get_sensitive()
            text, _ = w.export.prepared
            ext = 'md' if phase == 'save-markdown' else 'json'
            if ext == 'json':
                assert json.loads(text)['app']['version'] == __version__
            else:
                assert text.startswith('# Acelip Scope ' + __version__)
            w.save_text = lambda text, _: (PROJECT / 'var' / f'v14-{args.label}-export.{ext}').write_text(text)
            w.export.save.emit('clicked')
            assert (PROJECT / 'var' / f'v14-{args.label}-export.{ext}').read_text() == text
            record['export_' + ext] = 'PASS'
            if ext == 'md':
                w.export.format.set_selected(1)
                assert not w.export.save.get_sensitive()
                w.export.build_preview()
                phase = 'save-json'
            else:
                w.export.set_expanded(False)
                w.sharing_test.set_expanded(False)
                w.show_page('overview')
                w.scroll.get_vadjustment().set_value(0)
                w.set_default_size(1920, 1000)
                phase = 'wide'
        elif phase == 'wide':
            capture(w, '')
            w.set_default_size(720, 800)
            phase = 'compact'
        elif phase == 'compact':
            capture(w, '-compact')
            assert not errors, errors
            assert len(app.get_windows()) == 1
            record['privacy_ai_consent_sharing_cancel'] = 'PASS: existing UI smoke assertions'
            record['result'] = 'PASS'
            passed = True
            w.close()
            app.quit()
            return False
    except Exception:
        traceback.print_exc()
        record['result'] = 'FAIL'
        app.quit()
        return False
    return True


def setup(_):
    # Retain exercise_smoke assertions but let this harness own completion.
    app.get_active_window().smoke_finish = lambda: False
    GLib.timeout_add(600, tick)


app.connect_after('activate', setup)
app.run(['lucy-gui-acceptance'])
(PROJECT / 'var' / f'v14-{args.label}-gui.json').write_text(json.dumps(record, indent=2) + '\n')
qa.cleanup()
raise SystemExit(0 if passed else 1)
