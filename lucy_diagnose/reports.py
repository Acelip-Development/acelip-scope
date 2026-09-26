"""Plain text report format shared by all export and analysis actions."""

from .identity import DISPLAY_NAME
from .models import Status


def render_report(snapshot):
    counts = snapshot.counts()
    lines = [f'{DISPLAY_NAME} · read-only diagnostic report', '=' * 50,
             f'Mode: {snapshot.mode}', f'Started: {snapshot.started.isoformat(timespec="seconds")}',
             f'Finished: {snapshot.finished.isoformat(timespec="seconds") if snapshot.finished else "In progress"}',
             f'Scan status: {"CANCELLED / PARTIAL" if snapshot.cancelled else "Completed"}',
             ' · '.join(f'{s.value}: {counts[s.value]}' for s in Status), '',
             'Unavailable checks do not establish health or failure. No repairs or elevation were attempted.',
             'Reports may contain IP addresses, usernames, device paths, model names, and journal messages.', '']
    groups = [('ERRORS', {Status.ERROR}), ('WARNINGS', {Status.WARNING}),
              ('UNAVAILABLE CHECKS', {Status.UNAVAILABLE}), ('INFORMATION / PASSED CHECKS', {Status.INFO, Status.OK})]
    for heading, statuses in groups:
        lines.extend([heading, '-' * len(heading)])
        found = False
        for section, checks in snapshot.sections.items():
            for check in checks:
                if check.status not in statuses:
                    continue
                found = True
                lines.append(f'[{check.status.value.upper()}] {section} / {check.title}: {check.summary}')
                lines.append(f'  Coverage: {check.support.value}')
                if check.source:
                    lines.append(f'  Source: {check.source}')
                if check.observed_at:
                    lines.append(f'  Observed: {check.observed_at.isoformat(timespec="seconds")}')
                if check.details:
                    lines.extend('  ' + line for line in check.details.splitlines())
                lines.append('')
        if not found:
            lines.extend(['None reported.', ''])
    return '\n'.join(lines)
