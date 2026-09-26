"""Explicit read-only acceptance run on the current Linux environment.

Run inside each actual userspace/session; never substitutes os-release or tools.
Writes privacy-filtered exports and a compact evidence record only to --output.
Container evidence excludes desktop, hardware and the host kernel as distro proof.
"""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import platform
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lucy_diagnose import __version__
from lucy_diagnose.dashboard import DashboardState
from lucy_diagnose.exports import prepare_export
from lucy_diagnose.platform import get_platform
from lucy_diagnose.privacy import sanitize_report
from lucy_diagnose.scanner import MODES, scan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--environment', required=True, choices=('host', 'container', 'vm'))
    parser.add_argument('--missing-tools', action='store_true', help='Explicit empty-PATH degradation run')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=args.output / 'commands.log', level=logging.WARNING)
    if args.missing_tools:
        os.environ['PATH'] = ''
    backend = get_platform()
    runner = backend.create_runner()
    record = {'version': __version__, 'time': datetime.now().astimezone().isoformat(),
              'environment_type': args.environment, 'kernel': platform.release(),
              'python': platform.python_version(), 'distro': asdict(backend.get_distro_info()),
              'tool_environment': 'empty PATH (injected degradation)' if args.missing_tools else 'native PATH',
              'desktop': asdict(backend.get_desktop_info(runner)), 'scans': {},
              'gui': 'NOT TESTED by this CLI harness', 'capture': 'NOT TESTED; no capture initiated'}
    names = ('dpkg-query', 'apt-mark', 'rpm', 'dnf', 'pacman', 'zypper', 'flatpak', 'snap',
             'smartctl', 'sensors', 'wpctl', 'pactl', 'nmcli', 'lspci', 'journalctl', 'systemctl')
    record['commands'] = {name: asdict(backend.capabilities.find_command(name)) for name in names}
    record['packages'] = {name: [asdict(p) for p in backend.get_package_info(name, runner)]
                          for name in ('bash', 'discord', 'lucy-validation-nonexistent-package')}
    record['services'] = [asdict(backend.get_service_status(name, scope, runner))
                          for name, scope in (('dbus.service', 'system'), ('pipewire.service', 'user'),
                                              ('lucy-validation-nonexistent.service', 'user'))]
    record['process_only'] = asdict(backend.services.process('python3', runner))
    state = DashboardState()
    failed = []
    native_source = {'debian': 'deb', 'fedora-rhel': 'rpm', 'opensuse': 'rpm', 'arch': 'pacman'}.get(record['distro']['family'])
    if native_source and not args.missing_tools:
        # Independent positive/negative controls against the real native database.
        for name, expected in (('bash', True), ('lucy-validation-nonexistent-package', False)):
            native = next(p for p in record['packages'][name] if p['source'] == native_source)
            if native['installed'] is not expected:
                failed.append('native package ' + name)
    for mode in MODES:
        start = time.monotonic()
        snapshot = scan(mode, platform=backend)
        checks = [c for values in snapshot.sections.values() for c in values]
        errors = [c.title for c in checks if c.summary.startswith('Collector failed')]
        if errors:
            failed.append(mode)
        record['scans'][mode] = {'execution': 'FAIL' if errors else 'PASS',
                                 'seconds': round(time.monotonic() - start, 2),
                                 'checks': len(checks), 'severity': snapshot.counts(),
                                 'coverage': dict(Counter(c.support.value for c in checks)),
                                 'collector_failures': errors}
        state.merge(snapshot)
        print(mode, record['scans'][mode], flush=True)
    for format, extension in (('json', 'json'), ('markdown', 'md')):
        text, _ = prepare_export(state, format)
        (args.output / ('report.' + extension)).write_text(text)
        if format == 'json':
            assert json.loads(text)['app']['version'] == __version__
        else:
            assert text.startswith('# Acelip Scope ' + __version__)
    record['exports'] = 'PASS: JSON parsed, Markdown rendered, both saved with privacy filtering'
    record['observations'] = {section: [{'title': c.title, 'summary': c.summary,
                                       'status': c.status.value, 'support': c.support.value}
                                      for c in checks]
                              for section, checks in state.snapshot().sections.items()}
    readings, coverage = backend.get_sensor_status(runner)
    record['sensors'] = {'support': coverage, 'readings': [asdict(r) for r in readings]}
    sampler = backend.create_sampler()
    samples = [sampler.sample(runner)]
    time.sleep(.2)
    samples.append(sampler.sample(runner))
    record['telemetry'] = [asdict(sample) for sample in samples]
    cancel = threading.Event()
    cancel.set()
    cancelled = scan('Quick Scan', runner=backend.create_runner(cancel), platform=backend)
    record['pre_cancelled_scan'] = 'PASS' if cancelled.cancelled else 'FAIL'
    # Execute only a harmless Python sleep: validates actual bounded process cleanup.
    result = runner.run(sys.executable, '-c', 'import time; time.sleep(5)', timeout=.1)
    record['timeout'] = 'PASS' if 'Timed out' in result.problem else 'FAIL'
    if record['pre_cancelled_scan'] != 'PASS' or record['timeout'] != 'PASS':
        failed.append('runner')
    record['execution_result'] = 'FAIL' if failed else 'PASS'
    (args.output / 'evidence.json').write_text(sanitize_report(json.dumps(record, indent=2, default=str)) + '\n')
    print('EVIDENCE', args.output / 'evidence.json', record['execution_result'], flush=True)
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
