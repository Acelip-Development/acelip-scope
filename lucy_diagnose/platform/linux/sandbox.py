"""Conservative host coverage for the shipped minimal Flatpak permission profile.

The Linux backend owns this policy. Never infer an absent host service or package
from the private runtime, process namespace, or filtered session bus.
"""
from dataclasses import replace

from ...models import Check, Status, Support
from ...runtime import detect_runtime

RESTRICTION = 'This diagnostic is restricted by the Flatpak sandbox.'
HOST_COMMANDS = frozenset({'smartctl', 'lsblk', 'findmnt', 'systemctl', 'journalctl', 'ps',
    'nvidia-smi', 'sensors', 'wpctl', 'pactl', 'dpkg', 'dpkg-query', 'rpm', 'pacman',
    'snap', 'flatpak', 'ip', 'nmcli', 'ping', 'lspci', 'codex', 'claude', 'gemini', 'opencode'})


def restricted():
    return detect_runtime().restricted


def limitation(title, details=''):
    return Check(title, RESTRICTION, Status.UNAVAILABLE, details or RESTRICTION,
                 source='Flatpak permission profile', support=Support.UNAVAILABLE)


def portal_capability():
    # Properties.Get is read-only and NO_AUTO_START preserves dormant services.
    # No CreateSession, SelectSources, Start or OpenPipeWireRemote calls occur.
    try:
        from gi.repository import Gio, GLib
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        response = bus.call_sync('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop',
            'org.freedesktop.DBus.Properties', 'Get',
            GLib.Variant('(ss)', ('org.freedesktop.portal.ScreenCast', 'AvailableSourceTypes')),
            GLib.VariantType.new('(v)'), Gio.DBusCallFlags.NO_AUTO_START, 2500, None)
        mask = response.unpack()[0]
        if type(mask) is not int:
            raise ValueError('Invalid portal source mask')
        return Check('ScreenCast portal', 'Source types advertised' if mask else 'No sources advertised',
                     Status.INFO, f'AvailableSourceTypes={mask}. Capture remains unverified; explicit consent required.',
                     source='Desktop portal read-only property', support=Support.PARTIAL)
    except (ImportError, ValueError, OSError) as exc:
        return limitation('ScreenCast portal', f'Portal capability query unavailable ({type(exc).__name__}); capture unverified.')
    except Exception as exc:
        # GLib.Error is only available when GI imports successfully.
        return limitation('ScreenCast portal', f'Portal capability query unavailable ({type(exc).__name__}); capture unverified.')


def collect(section, runner):
    if section == 'Overview':
        from .overview import collect as overview
        checks = overview(runner)
        return [replace(c, title='Runtime operating system' if c.title == 'Operating system' else c.title,
                        support=Support.PARTIAL if c.status != Status.UNAVAILABLE else Support.UNAVAILABLE,
                        details=c.details + '\nSandbox-visible data only; incomplete host coverage. ' + RESTRICTION)
                for c in checks] + [limitation('Host access', '/proc exposes a private process namespace; CPU/memory counters and readable sysfs are partial observations.')]
    titles = {
        'Health': ('System services', 'User services', 'Journal', 'Package integrity'),
        'Storage': ('Host filesystems', 'Block devices', 'SMART devices', 'Disk sensors'),
        'Network': ('Network interfaces', 'Network reachability'),
        'AI Stack': ('Host AI packages', 'Host AI services'),
        'Discord / Screen Sharing': ('PipeWire host service', 'WirePlumber', 'Audio capabilities', 'Portal backends', 'Discord installation'),
    }
    checks = [limitation(title) for title in titles[section]]
    if section == 'Discord / Screen Sharing':
        checks += [portal_capability(), Check('Screen-sharing verification', 'Portal-based capture requires explicit consent; unverified',
                   details='Host backend identities and direct PipeWire sockets are not exposed. Use the desktop ScreenCast portal in the sharing application. Acelip Scope never starts capture.',
                   support=Support.PARTIAL)]
    return checks
