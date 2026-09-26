"""POSIX command previews only. These strings are never executed by the app."""
import shlex


def analysis_command(provider, model):
    file = shlex.quote('./lucy-analysis.txt')
    if provider == 'Codex':
        return f'codex exec --sandbox read-only - < {file}'
    if provider == 'Claude':
        return f'claude --print --tools "" < {file}'
    return f'OLLAMA_HOST=127.0.0.1:11434 ollama run {shlex.quote(model)} < {file}'
