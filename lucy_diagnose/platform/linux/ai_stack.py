import http.client
import json
from pathlib import Path
import shutil

from .common import unavailable
from .overview import collect_gpu
from ...models import Check, Status
from ...parsers import format_bytes


def ollama_get(endpoint):
    """Fixed loopback only. No proxy environment, redirects, generation, or pulls."""
    if endpoint not in {'/api/version', '/api/tags', '/api/ps'}:
        raise ValueError('Unsupported read-only Ollama endpoint')
    connection = http.client.HTTPConnection('127.0.0.1', 11434, timeout=3)
    try:
        connection.request('GET', endpoint, headers={'Accept': 'application/json'})
        response = connection.getresponse()
        raw = response.read(1048577)
        if len(raw) > 1048576:
            raise ValueError('Ollama response exceeds 1 MiB')
        if response.status != 200:
            raise ValueError(f'Ollama returned HTTP {response.status}')
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('Ollama response is not an object')
        return data
    finally:
        connection.close()


def collect(runner, get=ollama_get):
    checks = []
    for executable in ('codex', 'claude', 'gemini', 'opencode'):
        path = shutil.which(executable)
        if not path:
            checks.append(Check(executable.title(), 'Not found on PATH', Status.UNAVAILABLE))
            continue
        result = runner.run(executable, '--version', timeout=10)
        if result.ok and (result.stdout or result.stderr).strip():
            checks.append(Check(executable.title(), (result.stdout or result.stderr).strip(), Status.OK, path))
        else:
            checks.append(Check(executable.title(), 'Detected; version unavailable', Status.UNAVAILABLE, f'{path}\n{result.reason}'))
    result = runner.run('systemctl', 'show', 'ollama.service', '--no-pager',
                        '--property=LoadState,ActiveState,SubState,UnitFileState')
    if result.ok:
        state = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
        active = state.get('ActiveState', 'unknown')
        checks.append(Check('Ollama service', f"{active} · {state.get('SubState', 'unknown')}",
                            Status.OK if active == 'active' else Status.WARNING,
                            result.stdout.strip()))
    else:
        checks.append(unavailable('Ollama service', result))
    for endpoint, title in [('/api/version', 'Ollama API'), ('/api/tags', 'Ollama models'), ('/api/ps', 'Ollama loaded models')]:
        if runner.cancel.is_set():
            break
        try:
            data = get(endpoint)
            if endpoint == '/api/version':
                checks.append(Check(title, f"Available · {data.get('version', 'unknown version')}", Status.OK,
                                    'http://127.0.0.1:11434'))
            else:
                models = data.get('models', [])
                details = '\n'.join(f"{m.get('name', m.get('model', '?'))} · {format_bytes(m.get('size', 0))}"
                                    + (f" · VRAM {format_bytes(m['size_vram'])}" if 'size_vram' in m else '') for m in models)
                checks.append(Check(title, f'{len(models)} models' if models else 'No models reported', Status.INFO, details))
        except (OSError, ValueError, http.client.HTTPException, TypeError, AttributeError) as exc:
            checks.append(Check(title, 'Loopback API unavailable', Status.UNAVAILABLE, str(exc)))
    candidates = [shutil.which(name) for name in ('lm-studio', 'lmstudio', 'lms')]
    candidates += [str(p) for p in (Path.home() / '.lmstudio/bin/lms', Path('/opt/LM Studio/lm-studio'),
                                   Path('/opt/lm-studio/lm-studio')) if p.is_file()]
    appdir = Path.home() / 'Applications'
    if appdir.is_dir():
        candidates += [str(p) for p in appdir.iterdir() if p.is_file() and 'lm' in p.name.lower()
                       and 'studio' in p.name.lower() and p.suffix.lower() == '.appimage']
    paths = list(dict.fromkeys(p for p in candidates if p))
    checks.append(Check('LM Studio executable / CLI', 'Detected' if paths else 'Not found in common locations',
                        Status.OK if paths else Status.UNAVAILABLE, '\n'.join(paths)))
    result = runner.run('ps', '-eo', 'comm=')
    if result.ok:
        processes = sorted({line.strip() for line in result.stdout.splitlines()
                            if any(name in line.lower() for name in ('lm-studio', 'lm studio', 'lmstudio', 'llmster'))})
        checks.append(Check('LM Studio process', ', '.join(processes) if processes else 'Not detected',
                            details='Process-name detection is best effort; AppImage names may differ.'))
    else:
        checks.append(unavailable('LM Studio process', result))
    gpu = collect_gpu(runner)
    available = any(c.title in {'GPU', 'GPU 1 · GPU'} and c.status == Status.OK for c in gpu)
    checks.append(Check('NVIDIA inference readiness', 'GPU visible to NVIDIA management tools' if available else 'GPU visibility could not be confirmed',
                        Status.OK if available else Status.UNAVAILABLE,
                        'This verifies driver visibility only. No model is loaded and no inference is run. Backend compatibility and free VRAM still matter.\n'
                        + '\n'.join(f'{c.title}: {c.summary}' for c in gpu)))
    return checks
