"""User-operated save/portal validation. Never automatically captures or plays audio.

Run explicitly from source or the packaged validation directory. Every save
requires a user-operated picker; portal session creation requires a button click.
No PipeWire remote is opened and no image/video frames are read or persisted.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

base = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base if (base / 'lucy_diagnose').exists() else base.parent))
from lucy_diagnose.ui.application import Adw, Gio, Gtk
from gi.repository import GLib
from lucy_diagnose.ui.file_save import ReportSaver
from lucy_diagnose.runtime import build_info
from lucy_diagnose.identity import DISPLAY_NAME, APP_ID

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
record_path = args.output / 'manual-validation.json'
if record_path.exists():
    parser.error('Use a new output directory to preserve prior manual evidence')
record = {'build': build_info(platform_name='Linux'), 'events': [],
          'actual_capture': 'INCONCLUSIVE: no frames read; this validates chooser/session negotiation only',
          'actual_playback': 'NOT TESTED: application has no playback subsystem'}
app = Adw.Application(application_id=APP_ID + '.ManualValidation', flags=Gio.ApplicationFlags.NON_UNIQUE)
session, pending, bus, window = None, {}, None, None


def note(kind, message):
    record['events'].append({'at': datetime.now(timezone.utc).isoformat(), 'kind': kind, 'result': message})
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    status.set_text(message)


def close_capture(*_):
    global session
    if bus:
        for path in list(pending):
            bus.call('org.freedesktop.portal.Desktop', path, 'org.freedesktop.portal.Request', 'Close',
                     None, None, Gio.DBusCallFlags.NO_AUTO_START, 2000, None, None)
        pending.clear()
        if session:
            bus.call('org.freedesktop.portal.Desktop', session, 'org.freedesktop.portal.Session', 'Close',
                     None, None, Gio.DBusCallFlags.NO_AUTO_START, 2000, None, None)
            session = None
    return False


def request(method, variant, options, callback):
    token = 'lucy_' + uuid.uuid4().hex
    options['handle_token'] = GLib.Variant('s', token)
    sender = bus.get_unique_name()[1:].replace('.', '_')
    path = '/org/freedesktop/portal/desktop/request/' + sender + '/' + token
    pending[path] = callback
    def returned(connection, result):
        try:
            connection.call_finish(result)
        except GLib.Error as exc:
            pending.pop(path, None)
            note('portal', 'INCONCLUSIVE: ' + exc.message)
            close_capture()
    bus.call('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop',
             'org.freedesktop.portal.ScreenCast', method, variant(options), GLib.VariantType.new('(o)'),
             Gio.DBusCallFlags.NONE, 15000, None, returned)


def begin_capture(_):
    global bus
    if pending or session:
        return
    note('portal', 'User clicked portal test; no frames will be consumed')
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    except GLib.Error as exc:
        note('portal', 'INCONCLUSIVE: session bus unavailable')
        return
    def response(connection, sender, path, interface, signal, params):
        callback = pending.pop(path, None)
        if callback:
            code, results = params.unpack()
            if code:
                note('portal', 'CANCELLED by user' if code == 1 else 'INCONCLUSIVE: portal refused the request')
                close_capture()
            else:
                callback(results)
    bus.signal_subscribe('org.freedesktop.portal.Desktop', 'org.freedesktop.portal.Request', 'Response',
                         None, None, Gio.DBusSignalFlags.NONE, response)
    def started(results):
        streams = results.get('streams', [])
        note('portal', f'Chooser/session negotiation returned {len(streams)} streams; frames unverified, closing session')
        close_capture()
    def selected(results):
        request('Start', lambda options: GLib.Variant('(osa{sv})', (session, '', options)), {}, started)
    def created(results):
        global session
        session = results['session_handle']
        request('SelectSources', lambda options: GLib.Variant('(oa{sv})', (session, options)),
                {'types': GLib.Variant('u', 1), 'multiple': GLib.Variant('b', False), 'persist_mode': GLib.Variant('u', 0)}, selected)
    request('CreateSession', lambda options: GLib.Variant('(a{sv})', (options,)),
            {'session_handle_token': GLib.Variant('s', 'lucy_' + uuid.uuid4().hex)}, created)


def activate(_):
    global window, status
    window = Adw.ApplicationWindow(application=app, title=DISPLAY_NAME + ' · manual validation', default_width=640, default_height=560)
    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    for side in ('top','bottom','start','end'):
        getattr(content, 'set_margin_' + side)(24)
    content.append(Gtk.Label(label='User-operated validation · synthetic test report', css_classes=['title-2'], wrap=True))
    content.append(Gtk.Label(label='Save Markdown and JSON with fresh test filenames. Then save over one test file: cancel the replacement first, then confirm it. Try Cancel in the file picker. Only use files created for this test.', wrap=True, xalign=0))
    status = Gtk.Label(label='Ready. Nothing has been saved or captured.', wrap=True, xalign=0, selectable=True)
    saver = ReportSaver(window, lambda message: note('save-result', message))
    for extension, text in [('md', '# LUCY validation\n\nSynthetic report, no host data.\n'), ('json', '{"validation":"synthetic","host_data":false}\n')]:
        button = Gtk.Button(label='Save test ' + ('Markdown' if extension == 'md' else 'JSON') + '…')
        def save(_, extension=extension, text=text):
            note('save-action', 'User requested ' + extension + ' picker')
            saver.choose(text, 'lucy-v16-manual-test.' + extension)
        button.connect('clicked', save)
        content.append(button)
    content.append(Gtk.Separator())
    content.append(Gtk.Label(label='Optional portal test: click below, then select or cancel in the desktop chooser. Any returned session is closed immediately. No frames are read and no screen data is saved.', wrap=True, xalign=0))
    start = Gtk.Button(label='Open screen-sharing portal (optional)')
    start.connect('clicked', begin_capture)
    content.append(start)
    stop = Gtk.Button(label='Cancel / close portal session')
    stop.connect('clicked', lambda *_: (close_capture(), note('portal', 'User cancelled/closed the session')))
    content.append(stop)
    content.append(status)
    done = Gtk.Button(label='Finish validation')
    done.connect('clicked', lambda *_: window.close())
    content.append(done)
    window.set_content(content)
    def closed(*_):
        close_capture()
        note('completion', 'User closed the manual validation window')
        app.quit()
        return False
    window.connect('close-request', closed)
    window.present()
    note('launch', 'Manual validation window opened; awaiting user actions')


app.connect('activate', activate)
raise SystemExit(app.run(['lucy-manual-validation']))
