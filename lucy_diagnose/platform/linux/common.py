import json
from pathlib import Path

from ...models import Check, Status


def unavailable(title, result):
    from .sandbox import RESTRICTION
    if RESTRICTION in result.reason:
        return Check(title, RESTRICTION, Status.UNAVAILABLE, RESTRICTION, source='Flatpak permission profile')
    from ...errors import unavailable_message
    summary = unavailable_message(result.reason)
    return Check(title, summary, Status.UNAVAILABLE,
                 f"{result.reason}\nThis limits diagnostic coverage; it does not prove a host failure. Review the tool/access details before retrying. No elevation or repair was attempted.", source=' '.join(result.argv))


def read_text(path):
    return Path(path).read_text(errors='replace')


def json_result(title, result):
    if not result.ok:
        return None, unavailable(title, result)
    try:
        return json.loads(result.stdout), None
    except (ValueError, TypeError) as exc:
        return None, Check(title, 'Unrecognized command output', Status.UNAVAILABLE, str(exc))
