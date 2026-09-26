"""Inspect sharing prerequisites. Never create a capture session or start a service."""

import json
import os
import shutil

from .common import unavailable
from ..models import Check, Status

UNITS = ('pipewire.service', 'pipewire-pulse.service', 'wireplumber.service',
         'xdg-desktop-portal.service', 'xdg-desktop-portal-gnome.service')


def parse_units(text):
    return {fields['Id']: fields for block in text.strip().split('\n\n')
            if (fields := dict(line.split('=', 1) for line in block.splitlines() if '=' in line)) and 'Id' in fields}


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
    path = shutil.which('discord')
    checks.append(Check('Discord executable', path or 'Not detected on PATH', Status.INFO,
                        'Browser, Flatpak, and renamed installations may use other paths.', source='Executable lookup'))
    if shutil.which('flatpak'):
        result = runner.run('flatpak', 'info', '--show-version', 'com.discordapp.Discord', timeout=4)
        if result.ok:
            checks.append(Check('Discord Flatpak', result.stdout.strip(), Status.INFO, source='flatpak info com.discordapp.Discord'))
        elif result.problem or result.code != 1:
            checks.append(unavailable('Discord Flatpak', result))
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
