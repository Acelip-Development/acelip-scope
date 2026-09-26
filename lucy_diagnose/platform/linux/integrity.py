"""Bounded native file verification; never run package scripts or repairs."""
import re

from ...models import Check, Status, Support
from .common import unavailable


def verify_packages(runner, family):
    rpm = family in {'fedora-rhel', 'opensuse'}
    if not rpm and family != 'arch':
        return Check('Package integrity', f'File verification unsupported for {family}',
                     Status.UNAVAILABLE, support=Support.UNSUPPORTED)
    args = ('rpm', '-Va', '--noscripts', '--nodeps') if rpm else ('pacman', '-Qkk')
    result = runner.run(*args, timeout=20)
    source = ' '.join(args)
    scope = ('Installed RPM files only; verification scripts and dependency checks disabled.' if rpm else
             'Installed pacman files/mtree metadata only; this is not a content-digest audit.')
    scope += ' Differences can be intentional configuration or container extraction artifacts. No repair attempted.'
    output = '\n'.join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.problem:
        if result.stdout.strip() and any(word in result.problem for word in ('Timed out', 'truncated')):
            return Check('Package integrity', 'Verification incomplete', Status.UNAVAILABLE,
                         scope + '\n' + result.problem + '\n' + output, source=source, support=Support.PARTIAL)
        return unavailable('Package integrity', result)
    lines = result.stdout.splitlines()
    if rpm:
        # Differences return 1. Other failures or unknown output must never be
        # interpreted as a clean verification. stderr can contain read failures.
        valid = all(re.match(r'^(?:[.SM5DLUGTP?]{9}\s+|missing\s+)', line) for line in lines)
        if result.code not in (0, 1) or not valid or (result.code == 1 and not lines):
            return unavailable('Package integrity', result)
        differences = len(lines)
        partial = bool(result.stderr.strip()) or any('?' in line[:9] for line in lines)
    else:
        rows = [re.fullmatch(r'.+: (\d+) total files, (\d+) altered files', line) for line in lines]
        summaries = [row for row in rows if row]
        # Backup-file notices can accompany a valid summary. A missing mtree,
        # parse failure or permission failure prevents complete-coverage claims.
        if result.code not in (0, 1) or not summaries:
            return unavailable('Package integrity', result)
        differences = sum(int(row[2]) for row in summaries)
        if result.code == 1 and not differences:
            return unavailable('Package integrity', result)
        partial = True  # mtree/presence checks do not establish content integrity.
    support = Support.PARTIAL if partial else Support.SUPPORTED
    summary = (f'{differences} file differences reported' if differences else
               'No file differences reported' if not partial else 'No file differences reported in inspected scope')
    return Check('Package integrity', summary, Status.WARNING if differences else Status.INFO if partial else Status.OK,
                 scope + '\n' + output, source=source, count=differences, support=support)
