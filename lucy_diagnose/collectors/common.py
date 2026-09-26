import json
from pathlib import Path

from ..models import Check, Status


def unavailable(title, result):
    return Check(title, 'Check unavailable', Status.UNAVAILABLE,
                 f"{result.reason}\nNo elevation or repair was attempted.")


def read_text(path):
    return Path(path).read_text(errors='replace')


def json_result(title, result):
    if not result.ok:
        return None, unavailable(title, result)
    try:
        return json.loads(result.stdout), None
    except (ValueError, TypeError) as exc:
        return None, Check(title, 'Unrecognized command output', Status.UNAVAILABLE, str(exc))
