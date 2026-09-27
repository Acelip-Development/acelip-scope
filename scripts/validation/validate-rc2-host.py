"""Explicit real-host RC2 source UI acceptance; no installation or portal capture.

Uses isolated preferences and a NON_UNIQUE source application so the installed
RC1 Flatpak is never replaced or activated. Writes only the requested QA folder.
Screenshots render this application's widgets, never other desktop windows.
"""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from lucy_diagnose import __version__
from lucy_diagnose.ui.application import LucyApplication, Gtk, Gdk
from gi.repository import GLib

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
if any(args.output.iterdir()): parser.error('Output directory must be empty')
if not Gtk.init_check() or Gdk.Display.get_default() is None: raise SystemExit('GTK display unavailable')
app=LucyApplication(smoke_test=True)
app.smoke_test=False
app.preferences_path=args.output/'preferences.json'
record={'version':__version__,'data':'REAL HOST','backend':Gdk.Display.get_default().__class__.__name__,
        'installation':'Source; installed public RC1 Flatpak unchanged','capture':'App widgets only; no portal capture or frames',
        'screenshots':[],'result':'FAIL'}
phase='scan'
started=time.monotonic()
first_count=0
before=None


def capture(w,name):
    snap=Gtk.Snapshot.new()
    Gtk.WidgetPaintable.new(w).snapshot(snap,w.get_width(),w.get_height())
    texture=w.get_renderer().render_texture(snap.to_node(),None)
    assert texture.save_to_png(str(args.output/name))
    record['screenshots'].append(name)


def tick():
    global phase,first_count,before
    w=app.get_active_window()
    try:
        if time.monotonic()-started>120: raise TimeoutError('Host validation deadline')
        if phase=='scan':
            if w.state.latest is None or w.scanning or len(w.history.samples)<3: return True
            w.window_title.set_subtitle(__version__+' · REAL HOST · source validation')
            w.set_default_size(1366,1000)
            assert not any(f.check.summary.startswith('Collector failed') for f in w.state.findings())
            record['scan_mode']=w.state.latest.mode
            record['counts']=w.state.counts()
            record['cpu_sensor']=w.metric_cards['cpu_temp'].note.get_text()
            assert 'k10temp / Tctl' in record['cpu_sensor'],record['cpu_sensor']
            record['cpu_temperature']=w.metric_cards['cpu_temp'].value.get_text()
            cooling=w.state.find('Cooling telemetry')
            cpu=w.state.find('CPU temperature')
            assert cooling and cpu and cooling is not cpu
            assert cooling.details and cpu.details
            record['cooling_summary']=cooling.summary
            record['cooling_details']=cooling.details
            record['cpu_details']=cpu.details
            assert 'pump' in cooling.details.lower() and 'fan' in cooling.details.lower()
            before=w.state.snapshot().to_dict()
            first_count=len(w.history.samples)
            phase='overview'
        elif phase=='overview':
            capture(w,'rc2-host-overview.png')
            w.view_findings.emit('clicked')
            phase='findings'
        elif phase=='findings':
            assert w.pages.get_visible_child_name()=='findings'
            assert w.severity.get_selected()==0
            w.subsystems['System'][2].emit('clicked')
            assert w.scope.get_selected()==1 and w.severity.get_selected()==1
            assert any(f.check.title=='Cooling telemetry' for f in w.state.filtered_findings(1,'System'))
            w.show_page('reports')
            w.export.build_preview()
            phase='reports'
        elif phase=='reports':
            if w.export.busy: return True
            assert w.export.prepared and w.export.save.get_sensitive()
            assert w.state.snapshot().to_dict()==before
            if len(w.history.samples)<first_count+2: return True
            record['navigation']='PASS: Overview, Findings, subsystem details, Reports; observations and timestamps unchanged; no additional scan'
            record['live_telemetry']='PASS: two-second samples continued across views; bounded memory-only history'
            record['sample_count']=len(w.history.samples)
            record['reports']='PASS: real-host sanitized preview prepared, not saved or copied'
            w.show_page('overview')
            record['result']='PASS'
            w.close();app.quit();return False
    except Exception as exc:
        record['failure']=type(exc).__name__+': '+str(exc)
        w.close();app.quit();return False
    return True


app.connect_after('activate',lambda *_:GLib.timeout_add(500,tick))
app.run(['acelip-scope-rc2-host-validation'])
app.settings.close()
(args.output/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
raise SystemExit(0 if record['result']=='PASS' else 1)
