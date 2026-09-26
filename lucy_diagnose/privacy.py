"""Conservative, best-effort filtering of copies for external AI previews.

Redaction is not an anonymity guarantee. Free-form logs can contain identifiers
that no pattern filter recognizes; the visible preview must still be reviewed.
"""

from dataclasses import dataclass
import getpass
import ipaddress
from pathlib import Path
import re
import socket


@dataclass(frozen=True)
class PrivacyContext:
    username: str = ''
    home: str = ''
    hostname: str = ''

    @classmethod
    def current(cls):
        return cls(getpass.getuser(), str(Path.home()), socket.gethostname())


def _mask_ip(match):
    value = match.group(0)
    try:
        address = ipaddress.ip_address(value)
        return '[LOCAL-IP]' if not address.is_global else value
    except ValueError:
        return value


def sanitize_report(report: str, context: PrivacyContext | None = None) -> str:
    """Return a new sanitized string; raw report objects are never modified."""
    context = context or PrivacyContext.current()
    text = str(report)
    # Multiline private keys must be removed before line-oriented filters.
    text = re.sub(r'-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----',
                  '[PRIVATE-KEY]', text, flags=re.S)
    text = re.sub(r'(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9+/_.=:-]+', 'Bearer [SECRET]', text)
    text = re.sub(r'(?i)\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{16,}|'
                  r'github_pat_[A-Za-z0-9_]{16,}|AIza[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|'
                  r'AKIA[A-Z0-9]{16})\b', '[SECRET]', text)
    text = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[SECRET]', text)
    labels = (r'(?:api[_ -]?key|access[_ -]?key|access[_ -]?token|refresh[_ -]?token|auth[_ -]?token|'
              r'token|secret|client[_ -]?secret|password|passwd|authorization|cookie|'
              r'serial(?:[_ -]?number)?|machine[_ -]?id|product[_ -]?uuid|wwn|'
              r'hostname|host[_ -]?name|ssid|bssid|device[_ -]?id)')
    text = re.sub(r'(?im)(["\']?\b(?:[A-Z][A-Z0-9]*_)*' + labels + r'["\']?\s*[:=]\s*)([^\n,}]+)',
                  lambda m: m.group(1) + '[REDACTED]', text)
    text = re.sub(r'(?im)(--(?:api-key|token|password|secret)\s+)(\S+)', r'\1[SECRET]', text)
    text = re.sub(r'(?i)(://)[^\s/@:]+:[^\s/@]+@', r'\1[CREDENTIALS]@', text)
    text = re.sub(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '[UUID]', text)
    text = re.sub(r'(?i)(?<![0-9a-f:])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f:])', '[MAC]', text)
    text = re.sub(r'(?i)\b(?:[0-9a-f]{2}-){5}[0-9a-f]{2}\b', '[MAC]', text)
    text = re.sub(r'(?i)\b[0-9a-f]{32,64}\b', '[IDENTIFIER]', text)
    text = re.sub(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])', _mask_ip, text)
    text = re.sub(r'(?i)(?<![\w:])(?:[0-9a-f]{0,4}:){2,}[0-9a-f]{0,4}(?![\w:])', _mask_ip, text)
    if context.home and context.home != '/':
        text = text.replace(context.home, '[HOME]')
    text = re.sub(r'/(?:home|Users)/[^/\s"\']+', '[HOME]', text)
    text = re.sub(r'/run/(?:media/[^/\s]+|user/\d+)', '/run/[USER]', text)
    text = re.sub(r'(?i)/dev/disk/by-(?:id|uuid|label)/[^\s"\']+', '/dev/disk/[IDENTIFIER]', text)
    text = re.sub(r'(?i)\b(?:[a-z0-9-]+\.)+(?:local|lan|internal)\b', '[LOCAL-HOST]', text)
    for value, replacement in ((context.hostname, '[HOST]'), (context.username, '[USER]')):
        if value:
            text = re.sub(r'(?<![\w-])' + re.escape(value) + r'(?![\w-])', lambda _: replacement, text, flags=re.I)
    return text
