"""Desktop/session facts; an expected portal backend is never treated as active."""
import os
import re
from ...models import DesktopInfo, Support

ENVIRONMENTS = {'gnome': 'GNOME', 'kde': 'KDE Plasma', 'plasma': 'KDE Plasma',
                'cinnamon': 'Cinnamon', 'x-cinnamon': 'Cinnamon', 'xfce': 'XFCE', 'xfce4': 'XFCE',
                'mate': 'MATE', 'lxqt': 'LXQt'}


def configure_ui_environment(project):
    # Process-local choices only. No global GTK, desktop, or driver settings.
    os.environ['GSETTINGS_BACKEND'] = 'memory'
    os.environ['XDG_CACHE_HOME'] = str(project / 'var/cache')
    os.environ.setdefault('GSK_RENDERER', 'cairo')


def detect_desktop(environ=None, portal_backend='unknown'):
    env = os.environ if environ is None else environ
    current = env.get('XDG_CURRENT_DESKTOP', '')
    session = env.get('XDG_SESSION_DESKTOP') or env.get('DESKTOP_SESSION', '')
    tokens = [part.lower() for part in re.split('[:;]', current) if part] + [session.lower()]
    desktop = next((ENVIRONMENTS[token] for token in tokens if token in ENVIRONMENTS), 'unknown')
    if desktop == 'unknown':
        desktop = next((name for token in tokens for key, name in ENVIRONMENTS.items()
                        if token in {key + '-wayland', key + '-xorg', key + '-x11'}), 'unknown')
    kind = env.get('XDG_SESSION_TYPE', '').lower()
    if not kind:
        kind = 'wayland' if env.get('WAYLAND_DISPLAY') else 'x11' if env.get('DISPLAY') else 'unknown'
    kind = kind if kind in {'wayland', 'x11'} else 'unknown'
    display = {'wayland': 'Wayland', 'x11': 'X11', 'unknown': 'unknown'}[kind]
    return DesktopInfo(desktop, kind, display, session or 'unknown', portal_backend,
                       Support.SUPPORTED if desktop != 'unknown' and kind != 'unknown' else Support.PARTIAL)


def owned_portal_backends(runner):
    result = runner.run('busctl', '--user', '--acquired', '--no-pager', '--no-legend', '--timeout=3', 'list', timeout=4)
    if not result.ok:
        return ()
    prefix = 'org.freedesktop.impl.portal.desktop.'
    return tuple(sorted({line.split()[0][len(prefix):] for line in result.stdout.splitlines()
                         if line.split() and line.split()[0].startswith(prefix)}))


def backend_for_desktop(desktop, owned):
    preferred = {'GNOME': 'gnome', 'KDE Plasma': 'kde', 'Cinnamon': 'xapp', 'XFCE': 'gtk', 'MATE': 'gtk', 'LXQt': 'lxqt'}.get(desktop)
    # Owned bus names establish availability, not ScreenCast method ownership.
    if preferred in owned:
        return preferred
    return owned[0] if len(owned) == 1 else 'unknown'
