"""Inspect sharing prerequisites. Never create a capture session or start a service."""

import json
import os
import shutil
import configparser
from pathlib import Path
import stat

from .common import unavailable
from ..models import Check, Status

UNITS = ('pipewire.service', 'pipewire-pulse.service', 'wireplumber.service',
         'xdg-desktop-portal.service', 'xdg-desktop-portal-gnome.service')


def parse_units(text):
    return {fields['Id']: fields for block in text.strip().split('\n\n')
            if (fields := dict(line.split('=', 1) for line in block.splitlines() if '=' in line)) and 'Id' in fields}


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


def package_checks(runner):
    """Metadata queries only: never execute Discord to obtain its version."""
    checks, detected = [], []
    queries = (('deb', 'dpkg-query', ('-W', '-f=${db:Status-Abbrev}\t${Version}\n', 'discord')),
               ('Snap', 'snap', ('list', 'discord')),
               ('Flatpak', 'flatpak', ('info', '--show-version', 'com.discordapp.Discord')))
    for kind, command, args in queries:
        if not shutil.which(command):
            checks.append(Check('Discord ' + kind, f'{command} not installed; source not checked', Status.UNAVAILABLE, source='Package metadata'))
            continue
        result = runner.run(command, *args, timeout=4)
        installed = result.ok and bool(result.stdout.strip())
        if kind == 'deb':
            installed = installed and result.stdout.startswith('ii')
        if installed:
            detected.append(kind)
            checks.append(Check('Discord ' + kind, result.stdout.strip(), Status.INFO, source=f'{command} package metadata'))
            if kind in {'Flatpak', 'Snap'}:
                permissions = runner.run('flatpak', 'info', '--show-permissions', 'com.discordapp.Discord', timeout=4) if kind == 'Flatpak' else runner.run('snap', 'connections', 'discord', timeout=4)
                checks.append(Check('Discord ' + kind + ' permissions', 'Inspectable sandbox permissions', Status.INFO, permissions.stdout,
                                    source=f'{command} permission metadata') if permissions.ok else unavailable('Discord ' + kind + ' permissions', permissions))
        elif result.problem or result.code not in (0, 1) or 'permission' in result.stderr.lower():
            checks.append(unavailable('Discord ' + kind, result))
        else:
            checks.append(Check('Discord ' + kind, 'Not installed / not registered in this package scope', source=f'{command} package metadata'))
    executable = shutil.which('discord')
    checks.append(Check('Discord installation source', ', '.join(detected) if detected else 'Other / unverified executable' if executable else 'Not detected',
                        details='Multiple installations may coexist. Package metadata does not identify which running process is active. '
                                'Browser, AppImage, renamed and alternate-profile installs may be undetected.', source='Package metadata / executable lookup'))
    if 'deb' in detected:
        checks.append(Check('Discord native sandbox', 'No Snap/Flatpak policy applies to the deb package',
                            details='Chromium sandbox flags and runtime confinement were not inspected; native installation does not prove sandbox security.', source='Diagnostic scope'))
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


def collect(runner):
    checks = [Check('Desktop session', f"{os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')} · {os.environ.get('XDG_SESSION_TYPE', 'unknown')}",
                    details='GNOME Wayland sharing normally uses the ScreenCast portal and PipeWire. Session type alone does not prove capture works.',
                    source='XDG_CURRENT_DESKTOP / XDG_SESSION_TYPE')]
    result = runner.run('systemctl', '--user', 'show', *UNITS, '--property=Id,LoadState,ActiveState,SubState', '--no-pager')
    if not result.ok:
        checks.append(unavailable('Sharing services', result))
    else:
        units = parse_units(result.stdout)
        for name in UNITS:
            data = units.get(name, {})
            active = data.get('ActiveState', 'unknown')
            status = (Status.UNAVAILABLE if not data or data.get('LoadState') == 'not-found' else
                      Status.ERROR if active == 'failed' else Status.OK if active == 'active' else Status.INFO)
            checks.append(Check(name, active, status,
                                f"Load: {data.get('LoadState', 'unknown')} · Substate: {data.get('SubState', 'unknown')}\n"
                                'Inactive on-demand services are not necessarily faulty. LUCY does not activate them.',
                                source=f'systemctl --user show {name}'))
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
    socket_state = runner.run('systemctl', '--user', 'show', 'pipewire.socket', '--property=Id,LoadState,ActiveState,SubState', '--no-pager')
    checks.append(Check('PipeWire socket unit', 'Read-only socket activation state', details=socket_state.stdout, source='systemctl --user show pipewire.socket') if socket_state.ok else unavailable('PipeWire socket unit', socket_state))
    checks.extend(package_checks(runner))
    if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
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
                        '--unit=xdg-desktop-portal.service', '--unit=xdg-desktop-portal-gnome.service',
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
                        'LUCY reads no Discord account data, tokens, messages, screen frames, or microphone content.', source='Diagnostic scope'))
    return checks
