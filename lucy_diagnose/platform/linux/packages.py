"""Normalized installed-package metadata. No installs, refreshes, or repair operations."""
from pathlib import Path
import re
from .capabilities import Capabilities
from .distro import detect_distro
from .runner import Runner
from ...models import PackageInfo, Support

FLATPAK_IDS = {'discord': 'com.discordapp.Discord'}
NATIVE = {'debian': ('deb', 'dpkg-query', 'dpkg'), 'fedora-rhel': ('rpm', 'rpm', 'rpm/dnf'),
          'arch': ('pacman', 'pacman', 'pacman'), 'opensuse': ('rpm', 'rpm', 'rpm/zypper')}


class Packages:
    def __init__(self, distro=None, capabilities=None):
        self.distro = distro
        self.capabilities = capabilities or Capabilities()

    def find(self, name, runner=None):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9+_.-]*', name):
            raise ValueError('Invalid package name')
        runner = runner or Runner()
        distro = self.distro or detect_distro()
        native = NATIVE.get(distro.family)
        managers = [native] if native else [item for item in (NATIVE['debian'], NATIVE['fedora-rhel'], NATIVE['arch'])
                                         if self.capabilities.find_command(item[1]).available]
        managers += [('Snap', 'snap', 'snap')]
        appid = FLATPAK_IDS.get(name, name if '.' in name else None)
        if appid:
            managers.append(('Flatpak', 'flatpak', 'flatpak'))
        found = []
        for source, command, manager in managers:
            capability = self.capabilities.find_command(command)
            if not capability.available:
                found.append(PackageInfo(name, source=source, package_manager=manager, support=Support.UNAVAILABLE,
                                         evidence=f'{command} not installed; source not checked'))
                continue
            args = {'deb': ('dpkg-query', '-W', '-f=${db:Status-Abbrev}\t${Version}\n', name),
                    'rpm': ('rpm', '-q', '--qf', '%{NAME}\t%{VERSION}-%{RELEASE}\n', '--', name),
                    'pacman': ('pacman', '-Q', '--', name), 'Snap': ('snap', 'list', name),
                    'Flatpak': ('flatpak', 'info', '--show-version', appid)}[source]
            result = runner.run(*args, timeout=4)
            diagnostic = (result.stderr + '\n' + result.stdout).lower().strip()
            known_absence = not diagnostic or any(word in diagnostic for word in ('not installed', 'not found', 'no matching', 'no installed', 'was not found'))
            if result.problem or result.code not in (0, 1) or 'permission' in diagnostic or (result.code == 1 and not known_absence):
                found.append(PackageInfo(name, source=source, package_manager=manager, support=Support.UNAVAILABLE, evidence=result.reason))
                continue
            version = None
            if result.ok:
                rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
                if source == 'Flatpak' and rows:
                    version = ' '.join(rows[0])
                elif source == 'deb' and rows and rows[0][0] == 'ii' and len(rows[0]) > 1:
                    version = rows[0][1]
                elif source != 'deb':
                    version = next((row[1] for row in rows if len(row) > 1 and row[0] == name), None)
            installed = version is not None
            # A successful but malformed response is not proof of absence.
            support = Support.SUPPORTED if installed or result.code == 1 or (source == 'deb' and result.stdout.startswith('rc')) else Support.UNKNOWN
            found.append(PackageInfo(name, version, source, manager, sandboxed=source in {'Snap', 'Flatpak'},
                                     confidence='high' if installed else 'unknown', support=support,
                                     installed=installed if support == Support.SUPPORTED else None, evidence=result.stdout.strip()))
        executable = self.capabilities.find_command(name)
        if executable.available and not any(item.installed for item in found):
            path = executable.path
            try:
                resolved = str(Path(path).resolve())
            except OSError:
                resolved = path
            source = 'AppImage' if resolved.lower().endswith('.appimage') else 'manual/unknown'
            found.append(PackageInfo(name, source=source, package_manager='none', install_path=path,
                                     confidence='low', support=Support.PARTIAL, installed=True,
                                     evidence='Executable on PATH; installation ownership and confinement unverified'))
        return found or [PackageInfo(name, support=Support.UNKNOWN, evidence='No supported package source identified')]

    def permissions(self, package, runner=None):
        runner = runner or Runner()
        if package.source == 'Flatpak':
            return runner.run('flatpak', 'info', '--show-permissions', FLATPAK_IDS.get(package.name, package.name), timeout=4)
        if package.source == 'Snap':
            return runner.run('snap', 'connections', package.name, timeout=4)
        return None
