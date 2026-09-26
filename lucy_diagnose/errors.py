"""Friendly unavailable explanations; technical evidence stays in check Details."""

def unavailable_message(reason):
    text = str(reason).casefold()
    if any(term in text for term in ('permission denied', 'operation not permitted', 'must be root', 'requires root')):
        return 'Permission denied · not elevated'
    if 'not installed' in text or 'command not found' in text:
        return 'Command not installed'
    if 'timed out' in text or 'timeout' in text:
        return 'Diagnostic timed out; try again when the system is less busy'
    if 'cancelled' in text:
        return 'Scan cancelled; run it again when ready'
    if 'network is unreachable' in text or 'connection refused' in text:
        return 'Connection unavailable; other diagnostics can continue'
    return 'Diagnostic unavailable; host health is unknown for this check'
