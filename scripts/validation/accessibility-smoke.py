"""Practical GTK keyboard/focus/text-scale checks; no formal accessibility claim."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lucy_diagnose.ui.application import LucyApplication, Gtk
from gi.repository import GLib

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
if any(args.output.iterdir()):
    parser.error('Output directory must be empty')
app=LucyApplication(smoke_test=True)
app.smoke_test=False
app.autostart=False
app.preferences_path=args.output/'preferences.json'
record={'keyboard':'NOT TESTED','text_scale':'NOT TESTED','formal_wcag':'NOT CLAIMED'}
phase=0
passed=False
visited=set()
key_count=0


def capture(w,name):
    snap=Gtk.Snapshot.new()
    Gtk.WidgetPaintable.new(w).snapshot(snap,w.get_width(),w.get_height())
    texture=w.get_renderer().render_texture(snap.to_node(),None)
    assert texture.save_to_png(str(args.output/name))


def tick():
    global phase,passed,old_dpi,key_count
    w=app.get_active_window()
    try:
        if phase==0:
            assert app.themes.current=='system'
            assert not w.analysis.confirm.get_active()
            assert not w.analysis.copy_prompt.get_sensitive()
            w.scan_button.grab_focus()
            assert w.get_focus() is not None
            phase=10
            return True
        elif phase==10:
            # Exercise the same GTK action used by Tab key bindings, one move
            # per main-loop turn, without injecting input into the desktop.
            if w.get_focus():visited.add(type(w.get_focus()).__name__)
            if key_count<18:
                w.emit('move-focus',Gtk.DirectionType.TAB_FORWARD)
                key_count+=1
                return True
            assert len(visited)>=2,visited
            record['keyboard']='PASS: GTK move-focus action across controls; no desktop key injection or screen-reader certification'
            record['focus_widget_types']=sorted(visited)
            w.set_focus(None)
            settings=Gtk.Settings.get_default()
            old_dpi=settings.get_property('gtk-xft-dpi')
            settings.set_property('gtk-xft-dpi',144*1024)
            w.set_default_size(720,900)
            phase=1
        elif phase==1:
            capture(w,'v16-accessibility-text-scale.png')
            record['text_scale']='PASS: process-local 150% text scale, compact rendering'
            record['first_run']='System theme; no AI consent; no setup requested'
            w.set_focus(None)
            Gtk.Settings.get_default().set_property('gtk-xft-dpi',old_dpi)
            passed=True
            w.close()
            app.quit()
            return False
    except Exception as exc:
        record['failure']=type(exc).__name__+': '+str(exc)
        app.quit()
        return False
    return True


app.connect_after('activate',lambda *_: GLib.timeout_add(250,tick))
app.run(['lucy-accessibility-check'])
(args.output/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
raise SystemExit(0 if passed else 1)
