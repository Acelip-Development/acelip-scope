"""Small local preferences only. No diagnostic data is ever written here."""

from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
from pathlib import Path
import tempfile
import threading

from .themes.catalog import DEFAULT_THEME, normalize_theme

from .runtime import state_directory

PREFERENCES_PATH = state_directory('config') / 'preferences.json'
DEFAULTS = {'theme': DEFAULT_THEME, 'live_graphs': True, 'report_privacy': 'sanitized'}


def validated(values):
    values = values if isinstance(values, dict) else {}
    privacy = values.get('report_privacy')
    return {'theme': normalize_theme(values.get('theme')),
            'live_graphs': values.get('live_graphs') if isinstance(values.get('live_graphs'), bool) else True,
            'report_privacy': privacy if isinstance(privacy, str) and privacy in {'sanitized', 'local'} else 'sanitized'}


class SettingsStore:
    def __init__(self, path=PREFERENCES_PATH, *, legacy_path=None):
        self.path = Path(path)
        self.last_error = None
        self.migration = 'not needed'
        # Native checkouts retain var/preferences.json. Flatpak retains its
        # provisional app ID, so the old XDG directory remains accessible.
        if legacy_path is None and self.path == PREFERENCES_PATH and self.path.parent.name == 'acelip-scope':
            legacy_path = self.path.parent.with_name('lucy-diagnose') / self.path.name
        migrated = self._migrate(Path(legacy_path)) if legacy_path is not None else None
        try:
            self.values = validated(json.loads(self.path.read_text()))
        except (OSError, ValueError):
            self.values = migrated if migrated is not None else dict(DEFAULTS)
        self._lock = threading.Lock()
        self._pending = None
        self._future = None
        self._writing = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='scope-preferences')

    def _migrate(self, legacy):
        # lexists includes dangling symlinks: never replace an existing new store.
        if os.path.lexists(self.path) or not legacy.is_file() or legacy.is_symlink():
            return None
        temporary = None
        try:
            original = legacy.read_bytes()
            values = json.loads(original)
            if not isinstance(values, dict):
                return None
            values = validated(values)
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd, temporary = tempfile.mkstemp(prefix='.scope-migration-', dir=self.path.parent)
            with os.fdopen(fd, 'w') as stream:
                json.dump(values, stream, indent=2)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
            # Publish atomically without overwriting a concurrently created file.
            os.link(temporary, self.path)
            self.migration = 'migrated'
            # Only retire the legacy file after verified durable publication.
            if legacy.read_bytes() == original and json.loads(self.path.read_text()) == values:
                legacy.unlink()
            return values
        except FileExistsError:
            return None
        except (OSError, ValueError) as exc:
            self.last_error = type(exc).__name__
            self.migration = 'retry needed'
            # Preserve legacy preferences in memory if storage is unwritable;
            # leave the source intact so the next launch can retry.
            return values if isinstance(locals().get('values'), dict) else None
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)

    def get(self, key):
        return self.values[key]

    def set(self, key, value):
        if key not in DEFAULTS:
            raise ValueError('Unsupported preference')
        self.values = validated({**self.values, key: value})
        with self._lock:
            self._pending = dict(self.values)
            if not self._writing:
                self._writing = True
                self._future = self._executor.submit(self._drain)

    def _drain(self):
        while True:
            with self._lock:
                pending, self._pending = self._pending, None
                if pending is None:
                    self._writing = False
                    return
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                fd, name = tempfile.mkstemp(prefix='.scope-preferences-', dir=self.path.parent)
                try:
                    with os.fdopen(fd, 'w') as stream:
                        json.dump(pending, stream, indent=2)
                        stream.write('\n')
                    os.replace(name, self.path)
                finally:
                    if os.path.exists(name):
                        os.unlink(name)
                self.last_error = None
            except OSError as exc:
                self.last_error = type(exc).__name__
                logging.getLogger(__name__).warning('Local preference save failed (%s)', type(exc).__name__)

    def flush(self, timeout=3):
        if self._future:
            self._future.result(timeout=timeout)

    def close(self):
        self.flush()
        self._executor.shutdown(wait=False)
