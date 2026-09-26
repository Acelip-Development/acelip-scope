import argparse
import json
import logging
from .identity import DISPLAY_NAME
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from . import __version__
from .runtime import state_directory, render_build_info
from .reports import render_report
from .scanner import MODES, scan
from .platform.detect import get_platform

PROJECT = Path(__file__).resolve().parent.parent


def configure_logging():
    try:
        directory = state_directory('state')
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        handler = RotatingFileHandler(directory / 'lucy-diagnose.log', maxBytes=262144, backupCount=1)
        (directory / 'lucy-diagnose.log').chmod(0o600)
        logging.basicConfig(handlers=[handler], level=logging.WARNING,
                            format='%(asctime)s %(levelname)s %(name)s %(message)s')
    except OSError:
        logging.basicConfig(level=logging.WARNING)


def main():
    parser = argparse.ArgumentParser(description=f'{DISPLAY_NAME} · read-only system diagnostics')
    parser.add_argument('--version', action='version', version=f'{DISPLAY_NAME} {__version__}')
    parser.add_argument('--scan', choices=MODES, help='Run a read-only scan without GTK')
    parser.add_argument('--json', action='store_true', help='Print structured CLI results')
    parser.add_argument('--smoke-test', action='store_true', help='Launch GTK, scan, exercise views, and exit')
    parser.add_argument('--build-info', action='store_true', help='Show package and build provenance')
    args = parser.parse_args()
    if args.build_info:
        print(render_build_info(platform_name=get_platform().name))
        return 0
    configure_logging()
    if args.scan:
        result = scan(args.scan)
        print(json.dumps(result.to_dict(), indent=2) if args.json else render_report(result))
        return 0
    try:
        get_platform().configure_ui_environment(PROJECT)
        from .ui.application import LucyApplication, Gdk, Gtk
    except (ImportError, ValueError, OSError, AssertionError) as exc:
        print(f'GTK runtime unavailable: {exc}\nRequired: GTK4, libadwaita, PyGObject and Pycairo. See README for platform availability.', file=sys.stderr)
        return 1
    if not Gtk.init_check() or Gdk.Display.get_default() is None:
        print('No accessible GTK display. Launch from your desktop session, or use --scan.', file=sys.stderr)
        return 1
    app = LucyApplication(smoke_test=args.smoke_test)
    result = app.run([sys.argv[0]])
    return (0 if app.smoke_passed else 1) if args.smoke_test else result


if __name__ == '__main__':
    raise SystemExit(main())
