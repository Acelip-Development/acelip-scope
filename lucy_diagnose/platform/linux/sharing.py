"""Inspect sharing prerequisites. Never create a capture session or start a service."""

import json
import os
import shutil
import configparser
from pathlib import Path
import stat

from .common import unavailable
from ...models import Check, Status, Support, ServiceStatus
from .packages import Packages
from .services import Services, parse_units, service_check
from .desktop import detect_desktop, owned_portal_backends, backend_for_desktop

UNITS = ('pipewire.service', 'pipewire-pulse.service', 'wireplumber.service',
         'xdg-desktop-portal.service', 'xdg-desktop-portal-gnome.service')


def portal_backends(directory=Path('/usr/share/xdg-desktop-portal/portals')):
    found = []
    try:
        for path in sorted(directory.glob('*.portal'))[:30]:
            parser = configparser.ConfigParser(interpolation=None)
            parser.read_string(path.read_text()[:32768])
            interfaces = parser.get('portal', 'Interfaces', fallback='')
            desktop = parser.get('portal', 'UseIn', fallback='selection configured by desktop')
            found.append(f'{path.stem}: ScreenCast={"ScreenCast" in interfaces}; desktop={desktop}')
    except (OSError, configparser.Error):
        return Check('Portal backends', 'Backend definitions unavailable', Status.UNAVAILABLE, source='Installed portal metadata')
    return Check('Portal backends', f'{len(found)} installed backend definitions' if found else 'No backend definitions detected',
                 Status.INFO if found else Status.UNAVAILABLE,
                 '\n'.join(found) + '\nInstalled metadata does not establish which backend owns the active session.', source='Installed portal metadata')


def package_checks(runner, packages=None):
    packages = packages or Packages()
    checks, detected = [], []
    for package in packages.find('discord', runner):
        title = 'Discord ' + package.source
        if package.installed:
            detected.append(package.source)
            checks.append(Check(title, package.version or package.install_path or 'Detected; version unknown',
                                details=f'Manager: {package.package_manager} · confidence: {package.confidence}\n{package.evidence}',
                                source='Package metadata', support=package.support))
            permissions = packages.permissions(package, runner)
            if permissions is not None:
                checks.append(Check(title + ' permissions', 'Inspectable sandbox permissions', details=permissions.stdout,
                                    source='Package sandbox metadata') if permissions.ok else unavailable(title + ' permissions', permissions))
        elif package.support == Support.SUPPORTED and package.installed is False:
            checks.append(Check(title, 'Not installed / not registered in this package scope', source='Package metadata'))
        else:
            checks.append(Check(title, package.evidence or 'Package state unknown', Status.UNAVAILABLE,
                                source='Package metadata', support=package.support))
    checks.append(Check('Discord installation source', ', '.join(detected) if detected else 'Not detected',
                        details='Multiple installations can coexist. Package metadata does not establish which running process is active.',
                        source='Normalized Linux package queries', support=Support.SUPPORTED if detected else Support.UNKNOWN))
    if any(item in detected for item in ('deb', 'rpm', 'pacman', 'manual/unknown', 'AppImage')):
        checks.append(Check('Discord native sandbox', 'Runtime confinement unverified',
                            details='Native package or executable discovery does not prove Chromium sandbox enforcement.',
                            source='Diagnostic scope', support=Support.PARTIAL))
    return checks


def pipewire_socket(runtime=None):
    runtime = runtime if runtime is not None else os.environ.get('XDG_RUNTIME_DIR')
    if not runtime:
        return Check('PipeWire socket', 'Runtime directory unavailable', Status.UNAVAILABLE, source='XDG_RUNTIME_DIR')
    try:
        present = stat.S_ISSOCK((Path(runtime) / 'pipewire-0').stat().st_mode)
        return Check('PipeWire socket', 'Socket exists; not connected by LUCY' if present else 'Expected path is not a socket',
                     Status.INFO if present else Status.WARNING,
                     'A filesystem socket does not prove a responsive PipeWire session. LUCY does not connect or trigger socket activation.', source='Runtime socket metadata')
    except OSError as exc:
        return Check('PipeWire socket', f'Unavailable: {type(exc).__name__}', Status.UNAVAILABLE, source='Runtime socket metadata')


def collect(runner, services=None, desktop=None, packages=None):
    services = services or Services()
    desktop = desktop or detect_desktop()
    checks = [Check('Desktop session', f'{desktop.environment} · {desktop.display_server}',
                    details=f'Session: {desktop.session_name}. Session type does not prove capture works.',
                    source='Desktop session environment', support=desktop.support)]
    backend_unit = {'GNOME': 'xdg-desktop-portal-gnome.service', 'KDE Plasma': 'plasma-xdg-desktop-portal-kde.service',
                    'Cinnamon': 'xdg-desktop-portal-xapp.service', 'XFCE': 'xdg-desktop-portal-gtk.service',
                    'MATE': 'xdg-desktop-portal-gtk.service', 'LXQt': 'xdg-desktop-portal-lxqt.service'}.get(desktop.environment)
    units = (*UNITS[:4], *((backend_unit,) if backend_unit else ()))
    states = services.get_many(units, 'user', runner)
    checks.extend(service_check(state) for state in states)
    wireplumber = next((s for s in states if s.name == 'wireplumber.service'), None)
    if not wireplumber or wireplumber.state != ServiceStatus.RUNNING:
        manager = services.get('pipewire-media-session.service', 'user', runner)
    else:
        manager = wireplumber
    checks.append(service_check(manager, 'Audio session manager'))
    # --auto-start=no prevents the property read from activating a dormant portal.
    result = runner.run('busctl', '--user', '--auto-start=no', '--allow-interactive-authorization=no',
                        '--timeout=3', '--json=short', 'get-property', 'org.freedesktop.portal.Desktop',
                        '/org/freedesktop/portal/desktop', 'org.freedesktop.portal.ScreenCast', 'AvailableSourceTypes', timeout=4)
    if not result.ok:
        checks.append(unavailable('ScreenCast portal', result))
    else:
        try:
            raw = json.loads(result.stdout)['data']
            mask = int(raw[0] if isinstance(raw, list) else raw)
            types = [name for bit, name in ((1, 'monitors'), (2, 'windows'), (4, 'virtual displays')) if mask & bit]
            checks.append(Check('ScreenCast portal', 'Supports ' + ', '.join(types) if types else 'No source types advertised',
                                Status.OK if types else Status.WARNING,
                                'Read-only capability query; no screen picker, recording, or capture session was opened.',
                                source='ScreenCast.AvailableSourceTypes · D-Bus property'))
        except (ValueError, KeyError, TypeError, IndexError):
            checks.append(Check('ScreenCast portal', 'Unrecognized capability response', Status.UNAVAILABLE,
                                source='ScreenCast.AvailableSourceTypes'))
    checks.extend((portal_backends(), pipewire_socket()))
    checks.append(service_check(services.get('pipewire.socket', 'user', runner), 'PipeWire socket unit'))
    checks.extend(package_checks(runner, packages))
    owned = owned_portal_backends(runner)
    backend = backend_for_desktop(desktop.environment, owned)
    checks.append(Check('Desktop portal backend', backend if backend != 'unknown' else 'Not identified',
                        details='Owned backend bus names: ' + (', '.join(owned) or 'none visible') +
                                '. Availability does not prove ScreenCast method ownership.',
                        source='User bus owned names', support=Support.PARTIAL if backend == 'unknown' else Support.SUPPORTED))
    if desktop.session_type == 'wayland':
        cast = next((c for c in checks if c.title == 'ScreenCast portal'), None)
        if cast and cast.status == Status.WARNING:
            checks.append(Check('Wayland capture prerequisites', 'Portal advertises no capture sources in this Wayland session', Status.WARNING,
                                'Discord normally needs a compatible ScreenCast portal and PipeWire. Backend selection, a dormant session, or a portal fault are possible causes; not a proven root cause.', source='Session type / portal capability correlation'))
    path = shutil.which('discord')
    checks.append(Check('Discord executable', path or 'Not detected on PATH', Status.INFO,
                        'Browser, Flatpak, and renamed installations may use other paths.', source='Executable lookup'))
    result = runner.run('ps', '-eo', 'comm=')
    if result.ok:
        names = sorted({line.strip() for line in result.stdout.splitlines() if 'discord' in line.lower() or 'vesktop' in line.lower()})
        checks.append(Check('Discord process', ', '.join(names) or 'Not running / not detected', Status.INFO,
                            'Process names do not reveal whether an active screen-sharing session works.', source='ps · process names only'))
    else:
        checks.append(unavailable('Discord process', result))
    result = runner.run('journalctl', '--user', '--unit=pipewire.service', '--unit=wireplumber.service',
                        '--unit=xdg-desktop-portal.service', *((f'--unit={backend_unit}',) if backend_unit else ()),
                        '--priority=err', '--since', '24 hours ago', '--lines=40', '--no-pager', '--quiet', '--output=short-iso')
    if result.ok:
        count = len(result.stdout.strip().splitlines())
        checks.append(Check('Sharing journal errors', f'{count} visible entries · last 24 hours',
                            Status.WARNING if count else Status.INFO, result.stdout.strip() or 'No accessible matching entries.',
                            source='journalctl --user · portal / PipeWire errors', count=count))
    else:
        checks.append(unavailable('Sharing journal errors', result))
    checks.append(Check('Screen-sharing verification', 'Prerequisites inspected; end-to-end sharing unverified', Status.INFO,
                        'Only an explicit manual sharing attempt can verify Discord capture, audio, and receiver output. '
                        'LUCY reads no Discord account data, tokens, messages, screen frames, or microphone content.', source='Diagnostic scope', support=Support.PARTIAL))
    return checks
