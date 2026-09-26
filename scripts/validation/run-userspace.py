"""Run an explicit command in a disposable rootless Bubblewrap userspace.

Default: read-only image, private process/network namespaces, no host devices,
sysfs, session bus or home. Only --output is writable. --setup permits image
writes/network for installing test dependencies inside the disposable image.
--wayland exposes only the current compositor socket for guest GTK rendering;
it does not create a second desktop session or validate its services.
"""
import argparse
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--setup', action='store_true')
    parser.add_argument('--wayland', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    project = Path(__file__).resolve().parents[2]
    # Prevent accidental use of host / as the writable setup target.
    if not (root.parent / 'image.json').is_file() or root.name != 'rootfs':
        parser.error('root must be a disposable image produced by pull-userspace.py')
    output.mkdir(parents=True, exist_ok=True)
    for name in ('work', 'sys', 'run', 'home', 'tmp', 'proc', 'dev'):
        (root / name).mkdir(exist_ok=True)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('an explicit command is required')
    invocation = ['bwrap', '--die-with-parent', '--unshare-all', '--uid', '0', '--gid', '0',
                  '--bind' if args.setup else '--ro-bind', str(root), '/',
                  '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--tmpfs', '/run',
                  '--tmpfs', '/home', '--tmpfs', '/sys', '--tmpfs', '/work',
                  '--clearenv', '--setenv', 'PATH', '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
                  '--setenv', 'HOME', '/home/validation', '--setenv', 'LC_ALL', 'C.UTF-8',
                  '--setenv', 'PYTHONDONTWRITEBYTECODE', '1', '--chdir', '/work']
    # Bind source files only: never expose .git, caches, other images or host reports.
    for name in ('lucy_diagnose', 'scripts', 'tests'):
        invocation += ['--ro-bind', str(project / name), '/work/' + name]
    invocation += ['--ro-bind', str(project / 'pyproject.toml'), '/work/pyproject.toml',
                   '--bind', str(output), '/work/var']
    if args.setup:
        invocation += ['--share-net', '--ro-bind', '/etc/resolv.conf', '/etc/resolv.conf']
    if args.wayland:
        socket = Path(os.environ['XDG_RUNTIME_DIR']) / os.environ['WAYLAND_DISPLAY']
        invocation += ['--dir', '/run/user/0', '--ro-bind', str(socket), '/run/user/0/wayland-0',
                       '--setenv', 'XDG_RUNTIME_DIR', '/run/user/0', '--setenv', 'WAYLAND_DISPLAY', 'wayland-0',
                       '--setenv', 'XDG_SESSION_TYPE', 'wayland', '--setenv', 'GDK_BACKEND', 'wayland']
    return subprocess.call(invocation + ['--'] + command)


if __name__ == '__main__':
    raise SystemExit(main())
