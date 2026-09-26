from .common import unavailable
from .storage import filesystem_usage
from ...models import Check, Status, Support
from .distro import detect_distro
from .services import Services
from .integrity import verify_packages


def collect(runner, full=False, services=None, distro=None):
    checks = []
    services = services or Services()
    distro = distro or detect_distro()
    if not services.supported:
        checks.append(Check('Service inspection', 'No supported running service manager detected', Status.UNAVAILABLE,
                            source='Linux service manager discovery', support=Support.UNSUPPORTED))
        checks.extend(package_health(runner, distro, full))
        checks.append(Check('Journal inspection', 'System journal backend unsupported in this session', Status.UNAVAILABLE,
                            support=Support.UNSUPPORTED))
        checks.extend(c for c in filesystem_usage(runner) if c.status != Status.OK)
        return checks
    result = runner.run('systemctl', '--failed', '--no-legend', '--plain', '--no-pager')
    if result.ok:
        lines = result.stdout.strip().splitlines()
        checks.append(Check('Failed services / units', f'{len(lines)} failed units' if lines else 'No failed units',
                            Status.ERROR if lines else Status.OK, result.stdout.strip(), count=len(lines)))
    else:
        checks.append(unavailable('Failed services / units', result))
    checks.extend(package_health(runner, distro, full))
    since = '24 hours ago' if full else '1 hour ago'
    result = runner.run('journalctl', '--priority=err', '--since', since, '--lines=100', '--no-pager', '--quiet', '--output=short-iso')
    if result.ok:
        lines = result.stdout.strip().splitlines()
        checks.append(Check('Recent journal errors', f'{len(lines)} visible entries · {since}' if lines else f'No visible errors · {since}',
                            Status.WARNING if lines else Status.INFO, result.stdout.strip(), count=len(lines)))
    else:
        checks.append(unavailable('Recent journal errors', result))
    checks.append(Check('Journal coverage', 'Limited to entries accessible to the current user', Status.INFO,
                        'A quiet or empty journal is not proof of complete system coverage. Up to 100 error entries are shown.\n' + result.stderr.strip()))
    result = runner.run('journalctl', '--dmesg', '--since', '7 days ago', '--grep',
                        'Out of memory|oom-kill|Killed process|Memory cgroup out of memory',
                        '--case-sensitive=no', '--lines=50', '--no-pager', '--quiet', '--output=short-iso')
    # journalctl exits 1 when --grep finds no matching messages.
    if result.ok or (result.code == 1 and not result.problem and not result.stdout.strip() and not result.stderr.strip()):
        found = bool(result.stdout.strip())
        checks.append(Check('Recent OOM events', 'OOM events found' if found else 'No OOM events in the visible current-boot kernel journal',
                            Status.WARNING if found else Status.INFO,
                            'Search window: last 7 days, current boot only; up to 50 matches.\n' + result.stdout.strip()))
    else:
        checks.append(unavailable('Recent OOM events', result))
    checks.extend(c for c in filesystem_usage(runner) if c.status != Status.OK)
    return checks


def package_health(runner, distro, full=False):
    if distro.family in {'fedora-rhel', 'opensuse', 'arch'}:
        if not full:
            return [Check('Package integrity', 'File verification available in Full Scan',
                          details='Full file verification is omitted from Quick Scan.', support=Support.PARTIAL)]
        return [verify_packages(runner, distro.family)]
    if distro.family != 'debian':
        return [Check('Package database', f'Package integrity audit not implemented for {distro.family}', Status.UNAVAILABLE,
                      'Installed package metadata is available separately. No package-manager mutations are attempted.',
                      source='Linux package capabilities', support=Support.UNSUPPORTED)]
    checks = []
    for title, args, empty, status in [
        ('Package database', ('dpkg', '--audit'), 'No broken dpkg state reported', Status.ERROR),
        ('Held packages', ('apt-mark', 'showhold'), 'No held packages', Status.INFO),
    ]:
        result = runner.run(*args)
        checks.append(Check(title, f'{len(result.stdout.strip().splitlines())} report lines' if result.stdout.strip() else empty,
                            status if result.stdout.strip() else Status.OK, result.stdout.strip(), source=' '.join(args)) if result.ok else unavailable(title, result))
    return checks
