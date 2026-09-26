import argparse
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from . import __version__
from .reports import render_report
from .scanner import MODES, scan

PROJECT = Path(__file__).resolve().parent.parent


def configure_logging():
    try:
        directory = PROJECT / 'var'
        directory.mkdir(exist_ok=True, mode=0o700)
        handler = RotatingFileHandler(directory / 'lucy-diagnose.log', maxBytes=262144, backupCount=1)
        (directory / 'lucy-diagnose.log').chmod(0o600)
        logging.basicConfig(handlers=[handler], level=logging.WARNING,
                            format='%(asctime)s %(levelname)s %(name)s %(message)s')
    except OSError:
        logging.basicConfig(level=logging.WARNING)


def main():
    parser = argparse.ArgumentParser(description='LUCY Diagnose · read-only GNOME diagnostics')
    parser.add_argument('--version', action='version', version=f'LUCY Diagnose {__version__}')
    parser.add_argument('--scan', choices=MODES, help='Run a read-only scan without GTK')
    parser.add_argument('--json', action='store_true', help='Print structured CLI results')
    parser.add_argument('--smoke-test', action='store_true', help='Launch GTK, scan, exercise views, and exit')
    args = parser.parse_args()
    configure_logging()
    if args.scan:
        result = scan(args.scan)
        print(json.dumps(result.to_dict(), indent=2) if args.json else render_report(result))
        return 0
    try:
        # Keep toolkit settings ephemeral and caches within this checkout.
        os.environ['GSETTINGS_BACKEND'] = 'memory'
        os.environ['XDG_CACHE_HOME'] = str(PROJECT / 'var/cache')
        from .ui.application import LucyApplication, Gdk, Gtk
    except (ImportError, ValueError) as exc:
        print(f'GTK runtime unavailable: {exc}\nRequired: python3-gi gir1.2-gtk-4.0 gir1.2-adw-1', file=sys.stderr)
        return 1
    if not Gtk.init_check() or Gdk.Display.get_default() is None:
        print('No accessible GNOME display. Launch from your desktop session, or use --scan.', file=sys.stderr)
        return 1
    app = LucyApplication(smoke_test=args.smoke_test)
    result = app.run([sys.argv[0]])
    return (0 if app.smoke_passed else 1) if args.smoke_test else result


if __name__ == '__main__':
    raise SystemExit(main())
