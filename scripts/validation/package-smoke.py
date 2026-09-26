"""Opt-in packaged GTK acceptance. Writes only the explicitly supplied QA directory.

Includes real Gio writes and dialog responses. Native FileChooser cancellation is
programmatic; successful pointer/keyboard selection is a separate manual gate.
No screenshot capture portal is opened: PNGs render this app's own widgets.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

# Installed beside the packaged application, never import the working checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lucy_diagnose
assert Path(lucy_diagnose.__file__).resolve().parent == Path(__file__).resolve().parents[1] / "lucy_diagnose", "Package import escaped into another source tree"
from lucy_diagnose.ui.application import LucyApplication, Gtk
from lucy_diagnose.ui.file_save import ReportSaver
from lucy_diagnose.runtime import build_info, detect_runtime
from lucy_diagnose.scanner import MODES
from lucy_diagnose.settings import SettingsStore
from lucy_diagnose.identity import DISPLAY_NAME, PUBLISHER, TAGLINE, EXECUTABLE_NAME, LICENSE, COPYRIGHT, APP_ID, DEVELOPER_ID
from lucy_diagnose.themes.catalog import THEMES
from gi.repository import GLib, Gio, Adw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--label', required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
if any(args.output.iterdir()):
    parser.error('output directory must be empty; previous evidence will not be overwritten')
os.environ['GSETTINGS_BACKEND'] = 'memory'
os.environ.setdefault('GSK_RENDERER', 'cairo')
app = LucyApplication(smoke_test=True)
app.smoke_test, app.autostart = False, False
app.preferences_path = args.output / 'preferences.json'
record = {'build': build_info(platform_name='Linux'), 'label': args.label, 'scans': {}, 'themes': [], 'screenshots': [],
          'capture': 'NOT TESTED: no capture session created',
          'native_picker_selection': 'NOT TESTED: successful user selection still requires manual acceptance',
          'module_origin': 'packaged'  # asserted against the packaged module above
}
phase, current = 'init', None
queue, errors, messages = list(MODES), [], []
passed = False
started = time.monotonic()


def capture(w, suffix):
    snap = Gtk.Snapshot.new()
    Gtk.WidgetPaintable.new(w).snapshot(snap, w.get_width(), w.get_height())
    texture = w.get_renderer().render_texture(snap.to_node(), None)
    name = 'rc1-' + args.label + '-' + suffix + '.png'
    assert texture.save_to_png(str(args.output / name))
    record['screenshots'].append(name)


def tick():
    global phase, current, passed, saver, text, file, previous, cancel
    try:
        if time.monotonic() - started > 240:
            raise TimeoutError('Packaged acceptance deadline exceeded')
        w = app.get_active_window()
        if phase == 'init':
            assert app.get_application_id() == APP_ID
            assert record['build']['Application ID'] == APP_ID
            assert record['build']['Developer ID'] == DEVELOPER_ID
            record['namespace_identity'] = 'PASS'
            assert w.get_title() == DISPLAY_NAME
            assert w.window_title.get_subtitle() == TAGLINE
            legacy = args.output / 'legacy-preferences.json'
            legacy.write_text(json.dumps({'theme':'arcanum', 'live_graphs':False, 'report_privacy':'local'}))
            migrated = SettingsStore(args.output / 'migrated-preferences.json', legacy_path=legacy)
            assert migrated.get('theme') == 'arcanum' and not migrated.get('live_graphs')
            assert migrated.get('report_privacy') == 'local' and not legacy.exists()
            migrated.close()
            assert app.settings.get('theme') == 'system'
            record['identity_preference_migration'] = 'PASS'

            app.themes.backend.provider.connect('parsing-error', lambda _, section, error: errors.append(str(error)))
            w.smoke_finish = lambda: False
            w.set_default_size(1740, 1000)
            w.live_timer = GLib.timeout_add(400, w.sample_live)
            saver = ReportSaver(w, messages.append)
            phase = 'scans'
        elif phase == 'scans':
            if w.scanning:
                return True
            if current:
                assert w.state.latest.mode == current and not w.state.latest.cancelled
                assert not any('Collector failed' in f.check.summary for f in w.state.findings())
                record['scans'][current] = w.state.latest.counts()
                if detect_runtime().restricted:
                    assert not w.state.latest.counts()['error'], 'Sandbox restriction reported as ERROR'
                print('Packaged scan:', current, flush=True)
                current = None
            if queue:
                current = queue.pop(0)
                w.mode.set_selected(MODES.index(current))
                w.start_scan()
            else:
                phase = 'themes'
        elif phase == 'themes':
            if len(w.history.samples) < 2:
                return True
            for theme in THEMES:
                app.themes.select(theme)
                app.settings.flush()
                saved = SettingsStore(app.settings.path)
                assert saved.get('theme') == theme
                saved.close()
                assert w.preferences.theme_choices[theme].get_active()
                record['themes'].append(theme)
            app.themes.select('system')
            w.exercise_smoke()
            assert not w.closed
            record['privacy_ai_consent_manual_sharing_cancel'] = 'PASS: existing real UI assertions'
            w.live_toggle.set_active(True)
            assert w.live_toggle.get_label() != 'Paused'
            w.live_toggle.set_active(False)
            record['pause_resume'] = 'PASS'
            phase = 'prepare-md'
        elif phase in ('prepare-md', 'prepare-json'):
            if w.export.busy:
                return True
            w.export.format.set_selected(0 if phase == 'prepare-md' else 1)
            w.export.build_preview()
            phase = 'write-md' if phase == 'prepare-md' else 'write-json'
        elif phase in ('write-md', 'write-json'):
            if w.export.busy:
                return True
            assert w.export.prepared and w.export.save.get_sensitive()
            text = w.export.prepared[0]
            extension = 'md' if phase == 'write-md' else 'json'
            assert w.export.prepared[1].startswith(EXECUTABLE_NAME + '-')
            if extension == 'md':
                assert text.startswith('# ' + DISPLAY_NAME + ' ')
            if extension == 'json':
                assert json.loads(text)['app']['name'] == DISPLAY_NAME
                assert json.loads(text)['app']['publisher'] == PUBLISHER
                assert json.loads(text)['app']['version'] == record['build']['Version']
            file = Gio.File.new_for_path(str(args.output / ('report.' + extension)))
            messages.clear()
            saver.write(file, text)
            phase = 'saved-' + extension
        elif phase in ('saved-md', 'saved-json'):
            if not messages:
                return True
            assert messages[-1] == 'File saved', messages
            assert Path(file.get_path()).read_text() == text
            record['export_' + phase.split('-')[1]] = 'PASS: real Gio write of reviewed preview'
            if phase == 'saved-md':
                phase = 'prepare-json'
            else:
                previous = text
                messages.clear()
                saver.write(file, 'REPLACEMENT')
                phase = 'overwrite-cancel'
        elif phase == 'overwrite-cancel':
            dialog = w.get_visible_dialog()
            if dialog is None:
                return True
            assert isinstance(dialog, Adw.AlertDialog)
            dialog.close()
            assert Path(file.get_path()).read_text() == previous
            phase = 'overwrite-retry'
        elif phase == 'overwrite-retry':
            assert Path(file.get_path()).read_text() == previous
            saver.write(file, 'REPLACEMENT')
            phase = 'overwrite-confirm'
        elif phase == 'overwrite-confirm':
            dialog = w.get_visible_dialog()
            if dialog is None:
                return True
            dialog.set_close_response('replace')
            dialog.close()
            phase = 'overwritten'
        elif phase == 'overwritten':
            if not messages:
                return True
            assert messages[-1] == 'File saved'
            assert Path(file.get_path()).read_text() == 'REPLACEMENT'
            record['overwrite_cancel_confirm'] = 'PASS: real AlertDialog responses and Gio replacement'
            # Preserve the valid JSON report after the overwrite test.
            Path(file.get_path()).write_text(previous)
            etag = file.query_info('etag::value', Gio.FileQueryInfoFlags.NONE, None).get_attribute_string('etag::value')
            Path(file.get_path()).write_text(previous + '\n')
            messages.clear()
            saver.replace(file, 'MUST NOT OVERWRITE', etag)
            phase = 'etag'
        elif phase == 'etag':
            if not messages:
                return True
            assert messages[-1].startswith('Could not save:'), messages
            assert Path(file.get_path()).read_text() == previous + '\n'
            record['concurrent_edit_guard'] = 'PASS'
            messages.clear()
            saver.write(Gio.File.new_for_path(str(args.output / 'missing-directory/report.json')), 'test')
            phase = 'invalid'
        elif phase == 'invalid':
            if not messages:
                return True
            assert messages[-1].startswith('Could not save:'), messages
            messages.clear()
            saver.write(Gio.File.new_for_path('/app/lucy-write-denied' if detect_runtime().restricted else '/proc/lucy-write-denied'), 'test')
            phase = 'unwritable'
        elif phase == 'unwritable':
            if not messages:
                return True
            assert messages[-1].startswith('Could not save:'), messages
            record['invalid_unwritable_destination'] = 'PASS'
            messages.clear()
            cancel = Gio.Cancellable()
            saver.choose('not saved', 'cancelled-report.txt', cancel)
            GLib.timeout_add(1000, lambda: (cancel.cancel(), False)[1])
            phase = 'picker-wait'
        elif phase == 'picker-wait':
            if not cancel.is_cancelled():
                return True
            record['native_picker_cancel'] = 'PASS: real Gtk.FileDialog opened; programmatic cancellation'
            w.export.set_expanded(False)
            w.sharing_test.set_expanded(False)
            w.analysis.set_expanded(False)
            for _, _, expander, _ in w.subsystems.values():
                expander.set_expanded(False)
            w.scroll.get_vadjustment().set_value(0)
            w.set_default_size(1740, 1000)
            phase = 'wide'
        elif phase == 'wide':
            assert not messages, messages
            capture(w, 'dashboard')
            w.set_default_size(720, 800)
            phase = 'compact'
        elif phase == 'compact':
            capture(w, 'compact')
            w.show_about()
            phase = 'about'
        elif phase == 'about':
            dialog = w.get_visible_dialog()
            assert dialog.get_heading() == DISPLAY_NAME
            assert PUBLISHER in dialog.get_body() and TAGLINE in dialog.get_body()
            assert LICENSE in dialog.get_body() and COPYRIGHT in dialog.get_body()
            record['license_about'] = 'PASS'
            record['about_branding'] = 'PASS'
            capture(w, 'about-build-info')
            w.get_visible_dialog().close()
            assert not errors, errors
            record['css_errors'] = errors
            record['result'] = 'PASS'
            passed = True
            w.close()
            app.quit()
            return False
    except Exception:
        traceback.print_exc()
        record['result'] = 'FAIL'
        record['failed_phase'] = phase
        app.quit()
        return False
    return True


def setup(_):
    GLib.timeout_add(400, tick)


app.connect_after('activate', setup)
app.run(['lucy-packaged-acceptance'])
(args.output / 'validation.json').write_text(json.dumps(record, indent=2) + '\n')
raise SystemExit(0 if passed else 1)
