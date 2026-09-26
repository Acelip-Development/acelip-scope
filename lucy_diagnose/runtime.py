"""Package identity and path-free provenance; no host diagnostic probes."""
from dataclasses import dataclass
import json
import os
import platform
from pathlib import Path
import re

from . import __version__

from .identity import APP_ID
PROJECT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Runtime:
    package: str = 'Native'
    restricted: bool = False

    @property
    def host_access(self):
        return 'Restricted' if self.restricted else 'Current user permissions'


def detect_runtime(environ=None, flatpak_info=Path('/.flatpak-info')):
    env = os.environ if environ is None else environ
    if env.get('FLATPAK_ID') or flatpak_info.is_file():
        return Runtime('Flatpak', True)
    if env.get('APPIMAGE') or env.get('APPDIR'):
        return Runtime('AppImage')
    return Runtime()


def state_directory(kind, environ=None, runtime=None):
    env = os.environ if environ is None else environ
    runtime = runtime or detect_runtime(env)
    if runtime.package == 'Native':
        return PROJECT / 'var' / 'cache' if kind == 'cache' else PROJECT / 'var'
    fallback = {'config': '.config', 'state': '.local/state', 'cache': '.cache'}[kind]
    base = Path(env.get('XDG_' + kind.upper() + '_HOME') or Path.home() / fallback)
    if not base.is_absolute():
        base = Path.home() / fallback
    return base / 'lucy-diagnose'


def build_info(runtime=None, metadata_path=None, platform_name='Unknown'):
    runtime = runtime or detect_runtime()
    path = metadata_path or Path(__file__).with_name('_build.json')
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    commit = data.get('commit', '')
    commit = commit if isinstance(commit, str) and re.fullmatch(r'[a-f0-9]{40}', commit) else 'Unavailable (source checkout)'
    architecture = data.get('architecture', platform.machine())
    architecture = architecture if isinstance(architecture, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,32}', architecture) else 'Unknown'
    epoch = data.get('source_date_epoch')
    epoch = str(epoch) if type(epoch) is int and epoch >= 0 else 'Unstamped'
    return {'Architecture': architecture, 'Build epoch (SOURCE_DATE_EPOCH)': epoch, 'Version': __version__, 'Build type': 'Development' if __version__.endswith('-dev') else 'Release',
            'Git commit': commit, 'Source state': 'Modified' if data.get('dirty') else 'Clean' if data else 'Unstamped',
            'Packaging format': runtime.package, 'Runtime': data.get('runtime', 'Host') if data.get('runtime') in {'GNOME 50', 'Host'} else 'Host',
            'Platform backend': platform_name, 'Host access': runtime.host_access}


def render_build_info(**kwargs):
    return '\n'.join(f'{name}: {value}' for name, value in build_info(**kwargs).items())
