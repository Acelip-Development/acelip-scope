#!/usr/bin/env python3
"""Offline package builds from pinned, pre-existing dependencies. No installation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lucy_diagnose import __version__
from lucy_diagnose.identity import APP_ID, EXECUTABLE_NAME, LICENSE, COPYRIGHT

LOCK = json.loads((ROOT / 'packaging/runtime-lock.json').read_text())
MANIFEST = ROOT / 'packaging/flatpak' / (APP_ID + '.json')


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def output(*args):
    return run(*args, capture_output=True, text=True).stdout.strip()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def artifact_name(format, arch=None, version=__version__):
    arch = arch or platform.machine()
    if not re.fullmatch(r'[A-Za-z0-9_.+-]+', arch) or not re.fullmatch(r'[A-Za-z0-9_.+-]+', version):
        raise ValueError('Invalid artifact version or architecture')
    extension = {'Flatpak': 'flatpak', 'AppImage': 'AppImage'}[format]
    return f'{EXECUTABLE_NAME}-{version}-{arch}.{extension}'


def provenance():
    commit = os.environ.get('ACELIP_SCOPE_BUILD_COMMIT') or os.environ.get('LUCY_BUILD_COMMIT')
    epoch = os.environ.get('SOURCE_DATE_EPOCH')
    dirty = False
    if (ROOT / '.git').exists():
        commit = output('git', '-C', ROOT, 'rev-parse', 'HEAD')
        epoch = epoch or output('git', '-C', ROOT, 'show', '-s', '--format=%ct', 'HEAD')
        dirty = bool(output('git', '-C', ROOT, 'status', '--porcelain'))
    return {'license': LICENSE, 'copyright': COPYRIGHT, 'commit': commit or 'unavailable', 'dirty': dirty, 'runtime': 'GNOME 50',
            'architecture': platform.machine(), 'source_date_epoch': int(epoch or 0)}, int(epoch or 0)


def stage(prefix, format):
    prefix.mkdir(parents=True, exist_ok=True)
    application = prefix / 'share' / EXECUTABLE_NAME / 'lucy_diagnose'
    application.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'lucy_diagnose', application, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '_build.json'))
    notices = prefix / 'share/licenses' / EXECUTABLE_NAME
    notices.mkdir(parents=True, exist_ok=True)
    for name in ('LICENSE', 'NOTICE'):
        shutil.copyfile(ROOT / name, notices / name)
    validation = application.parent / 'validation'
    validation.mkdir()
    for name in ('package-smoke.py', 'manual-acceptance.py'):
        shutil.copyfile(ROOT / 'scripts/validation' / name, validation / name)
    data, _ = provenance()
    (application / '_build.json').write_text(json.dumps(data, sort_keys=True) + '\n')
    for directory, source, name in (
        ('applications', f'{APP_ID}.desktop', f'{APP_ID}.desktop'),
        ('metainfo', f'{APP_ID}.metainfo.xml', f'{APP_ID}.metainfo.xml'),
        ('icons/hicolor/scalable/apps', 'acelip-scope-symbolic.svg', f'{APP_ID}.svg')):
        target = prefix / 'share' / directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'data' / source, target)
    (prefix / 'bin').mkdir(exist_ok=True)
    launcher = prefix / 'bin' / EXECUTABLE_NAME
    launcher.write_text('#!/bin/sh\nexport PYTHONDONTWRITEBYTECODE=1\nexport PYTHONPATH=/app/share/acelip-scope\nexec /usr/bin/python3 -P -m lucy_diagnose "$@"\n')
    launcher.chmod(0o755)


def verify_runtime(arch):
    if arch not in LOCK:
        raise RuntimeError(f'BLOCKED: no reviewed runtime lock for architecture {arch}')
    if not shutil.which('flatpak'):
        raise RuntimeError('BLOCKED: flatpak CLI is required; no host packages were installed')
    ref = f'{LOCK["runtime"]}/{arch}/{LOCK["branch"]}'
    commit = output('flatpak', 'info', '--show-commit', ref)
    if commit != LOCK[arch]['commit']:
        raise RuntimeError(f'BLOCKED: runtime {ref} does not match packaging/runtime-lock.json')
    return Path(output('flatpak', 'info', '--show-location', ref)) / 'files'


def normalize_flatpak_bytes(contents, epoch):
    """Normalize only the unsigned OSTree delta's generation time, not its commit.

    Flatpak 1.16.6/libostree ignore SOURCE_DATE_EPOCH for this separate timestamp.
    Parse the documented superblock with GLib instead of editing byte offsets.
    Refuse malformed/new layouts; preserve every other serialized child exactly.
    https://ostreedev.github.io/ostree/formats/#the-delta-superblock
    """
    try:
        from gi.repository import GLib
    except ImportError as exc:
        raise RuntimeError('BLOCKED: build Python needs PyGObject/GLib for deterministic Flatpak bundles') from exc
    signature = '(a{sv}tayay(a{sv}aya(say)sstayay)aya(uayttay)a(yaytt))'
    value = GLib.Variant.new_from_bytes(GLib.VariantType.new(signature), GLib.Bytes.new(contents), False)
    if not value.is_normal_form() or value.get_child_value(3).n_children() != 32:
        raise ValueError('Unsupported or malformed unsigned Flatpak bundle')
    children = [value.get_child_value(i) for i in range(value.n_children())]
    children[1] = GLib.Variant.new_uint64(int.from_bytes(epoch.to_bytes(8, 'big'), sys.byteorder))
    normalized = GLib.Variant.new_tuple(*children)
    for index in (0, 2, 3, 4, 5, 6, 7):
        if normalized.get_child_value(index).get_data_as_bytes().get_data() != value.get_child_value(index).get_data_as_bytes().get_data():
            raise ValueError('Unexpected bundle metadata change')
    return normalized.get_data_as_bytes().get_data()


def normalize_license_links(root):
    """Keep upstream notice bytes intact and readable in a relocated AppImage."""
    licenses = root / 'share/licenses'
    for path in licenses.rglob('*'):
        if not path.is_symlink():
            continue
        target = path.readlink()
        if not target.is_absolute():
            continue
        if not str(target).startswith('/usr/share/licenses/'):
            raise ValueError('Unexpected absolute license link outside runtime notices')
        destination = root / str(target).removeprefix('/usr/')
        if not destination.is_file() or not destination.resolve().is_relative_to(licenses.resolve()):
            raise ValueError('Missing or unsafe runtime license link target')
        path.unlink()
        path.symlink_to(os.path.relpath(destination, path.parent))


def prune_appimage_runtime(root):
    manifest = json.loads((ROOT / 'packaging/appimage/prune.json').read_text())
    removed, names = [], set()
    for pattern in manifest['patterns']:
        if pattern.startswith('/') or '..' in Path(pattern).parts:
            raise ValueError('Unsafe runtime prune pattern')
        for path in sorted(root.glob(pattern)):
            if not path.parent.resolve().is_relative_to(root.resolve()):
                raise ValueError('Runtime prune path escapes staged copy')
            removed.append(path.relative_to(root).as_posix())
            names.add(path.name)
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
    # Check every retained ELF consumer, not just Python's immediate dependencies.
    # A reviewed family cannot disappear if another retained binary still needs it.
    for path in root.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                continue
        result = run('readelf', '-d', path, capture_output=True, text=True)
        needed = set(re.findall(r'\(NEEDED\).*?\[(.*?)\]', result.stdout))
        if needed & names:
            raise RuntimeError('Pruning broke a retained ELF dependency: ' + path.relative_to(root).as_posix())
    return sorted(removed)


def normalized_times(root, epoch):
    for path in [root, *root.rglob('*')]:
        os.utime(path, (epoch, epoch), follow_symlinks=False)


def checksums(directory):
    paths = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix in {'.flatpak', '.AppImage'})
    if not paths:
        raise RuntimeError('No package artifacts to checksum')
    text = ''.join(f'{digest(path)}  {path.name}\n' for path in paths)
    destination = directory / 'SHA256SUMS'
    # Existing matching manifests are allowed; differing ones require a new directory.
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or destination.read_text() != text:
            raise FileExistsError('Refusing to overwrite SHA256SUMS; use a new --dist directory')
    else:
        with destination.open('x') as stream:
            stream.write(text)
    for line in destination.read_text().splitlines():
        sha, name = line.split('  ', 1)
        if Path(name).name != name or digest(directory / name) != sha:
            raise RuntimeError('Checksum verification failed')
    print('Verified SHA256SUMS', flush=True)
    return text


def build(format, directory):
    arch = platform.machine()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / artifact_name(format, arch)
    if target.exists() or target.is_symlink() or (directory / 'SHA256SUMS').exists():
        raise FileExistsError(f'Refusing to overwrite artifacts in {directory}; use a new --dist directory')
    runtime = verify_runtime(arch)
    data, epoch = provenance()
    environment = {**os.environ, 'SOURCE_DATE_EPOCH': str(epoch), 'TZ': 'UTC', 'LC_ALL': 'C'}
    if format == 'AppImage':
        if not shutil.which('mksquashfs') or not shutil.which('readelf'):
            raise RuntimeError('BLOCKED: mksquashfs and readelf are required; no host packages were installed')
        appimage_runtime = Path(os.environ.get('APPIMAGE_RUNTIME', str(ROOT / 'var/packaging-tools' / ('runtime-' + arch))))
        if not appimage_runtime.is_file() or digest(appimage_runtime) != LOCK[arch]['appimage_runtime_sha256']:
            raise RuntimeError('BLOCKED: missing or mismatched AppImage runtime; set APPIMAGE_RUNTIME to the pinned runtime file (see PACKAGING.md)')
    build_root = ROOT / 'build/packaging'
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=format.lower() + '-', dir=build_root) as temp:
        temp = Path(temp)
        staged = temp / 'app'
        if format == 'Flatpak':
            # Pure Python: the existing Platform can serve as the build SDK;
            # no compiler, dependency downloads or flatpak-builder required.
            run('flatpak', 'build-init', staged, APP_ID, LOCK['runtime'], LOCK['runtime'], LOCK['branch'])
            stage(staged / 'files', format)
            finish = json.loads(MANIFEST.read_text())['finish-args']
            run('flatpak', 'build-finish', '--command=' + EXECUTABLE_NAME, *finish, staged)
            normalized_times(staged, epoch)
            repo = temp / 'repo'
            run('flatpak', 'build-export', '--timestamp=' + datetime.fromtimestamp(epoch, timezone.utc).isoformat(), repo, staged, 'devel', env=environment)
            package = temp / target.name
            run('flatpak', 'build-bundle', repo, package, APP_ID, 'devel', '--runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo', env=environment)
            package.write_bytes(normalize_flatpak_bytes(package.read_bytes(), epoch))
        else:
            stage(staged / 'usr', format)
            # Copy the pinned platform, then prune only reviewed unused families.
            # Do not use host Python, GTK, libadwaita or their development files.
            shutil.copytree(runtime, staged / 'runtime', symlinks=True)
            normalize_license_links(staged / 'runtime')
            removed = prune_appimage_runtime(staged / 'runtime')
            (staged / 'runtime-pruning.json').write_text(json.dumps({'removed': removed}, indent=2) + '\n')
            shutil.copyfile(ROOT / 'packaging/appimage/AppRun', staged / 'AppRun')
            (staged / 'AppRun').chmod(0o755)
            shutil.copyfile(ROOT / 'data' / (APP_ID + '.desktop'), staged / (APP_ID + '.desktop'))
            shutil.copyfile(ROOT / 'data/acelip-scope-symbolic.svg', staged / (APP_ID + '.svg'))
            (staged / '.DirIcon').symlink_to(APP_ID + '.svg')
            notices = staged / 'usr/share/licenses/acelip-scope'
            notices.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'packaging/licenses/appimage-runtime.LICENSE', notices / 'appimage-runtime.LICENSE')
            normalized_times(staged, epoch)
            squash = temp / 'filesystem.squashfs'
            run('mksquashfs', staged, squash, '-noappend', '-all-root', '-no-xattrs', '-comp', 'zstd',
                '-processors', '2', '-mkfs-time', str(epoch), '-all-time', str(epoch), '-no-progress',
                env={key: value for key, value in environment.items() if key != 'SOURCE_DATE_EPOCH'})
            package = temp / target.name
            with package.open('xb') as dest, appimage_runtime.open('rb') as runtime_file, squash.open('rb') as filesystem:
                shutil.copyfileobj(runtime_file, dest)
                shutil.copyfileobj(filesystem, dest)
            package.chmod(0o755)
        # Exclusive creation also protects against another build racing us.
        with package.open('rb') as source, target.open('xb') as destination:
            shutil.copyfileobj(source, destination)
        target.chmod(0o755 if format == 'AppImage' else 0o644)
    print(f'{target.name}: {target.stat().st_size} bytes; SHA256 {digest(target)}', flush=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('format', choices=['flatpak', 'appimage', 'all', 'checksums', 'stage'])
    parser.add_argument('--dist', type=Path, default=ROOT / 'dist')
    parser.add_argument('--prefix', type=Path)
    parser.add_argument('--format', dest='stage_format', choices=['Flatpak', 'AppImage'])
    args = parser.parse_args()
    if args.format == 'stage':
        if not args.prefix or not args.stage_format:
            parser.error('stage requires --prefix and --format')
        stage(args.prefix, args.stage_format)
        return
    if args.format != 'checksums':
        for format in (['Flatpak', 'AppImage'] if args.format == 'all' else [args.format.title().replace('Appimage', 'AppImage')]):
            build(format, args.dist)
    print(checksums(args.dist), end='')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Packaging stopped: {exc}', file=sys.stderr)
        raise SystemExit(1)
