import json
from pathlib import Path

from ...models import Check, Status


def unavailable(title, result):
    reason = result.reason.lower()
    summary = 'Permission denied · not elevated' if any(term in reason for term in (
        'permission denied', 'operation not permitted', 'must be root', 'requires root')) else (
        'Command not installed' if 'not installed' in reason else 'Check unavailable')
    return Check(title, summary, Status.UNAVAILABLE,
                 f"{result.reason}\nNo elevation or repair was attempted.", source=' '.join(result.argv))


def read_text(path):
    return Path(path).read_text(errors='replace')


def json_result(title, result):
    if not result.ok:
        return None, unavailable(title, result)
    try:
        return json.loads(result.stdout), None
    except (ValueError, TypeError) as exc:
        return None, Check(title, 'Unrecognized command output', Status.UNAVAILABLE, str(exc))
