import argparse
import json
import logging
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
        from .ui.application import LucyApplication
    except (ImportError, ValueError) as exc:
        print(f'GTK runtime unavailable: {exc}\nRequired: python3-gi gir1.2-gtk-4.0 gir1.2-adw-1', file=sys.stderr)
        return 1
    return LucyApplication(smoke_test=args.smoke_test).run([sys.argv[0]])


if __name__ == '__main__':
    raise SystemExit(main())
