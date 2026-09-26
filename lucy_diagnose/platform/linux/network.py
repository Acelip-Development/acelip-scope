from .common import json_result, read_text, unavailable
from ...models import Check, Status
from ...parsers import vpn_interfaces


def collect(runner):
    checks = []
    interfaces, error = json_result('Network interfaces', runner.run('ip', '-j', '-details', 'address', 'show'))
    if error:
        checks.append(error)
    else:
        for interface in interfaces:
            addresses = [f"{a.get('local')}/{a.get('prefixlen')} ({a.get('family')})" for a in interface.get('addr_info', [])]
            state = interface.get('operstate', 'UNKNOWN')
            checks.append(Check(f"Interface · {interface['ifname']}", state, Status.OK if state == 'UP' else Status.INFO,
                                '\n'.join(addresses) or 'No IP address reported'))
        vpns = vpn_interfaces(interfaces)
        checks.append(Check('VPN interfaces', ', '.join(vpns) or 'No tunnel interface detected', details=
                            'Detection uses interface types and common names. A tunnel interface does not prove that traffic is routed through a VPN.'))
    routes = []
    for family in ('-4', '-6'):
        data, error = json_result(f'Default route ({family})', runner.run('ip', '-j', family, 'route', 'show', 'default'))
        if error:
            checks.append(error)
        else:
            routes.extend(data)
            checks.append(Check(f'Default route ({family})', f'{len(data)} default routes' if data else 'No default route',
                                Status.INFO, '\n'.join(f"via {r.get('gateway', 'on-link')} dev {r.get('dev', '?')} metric {r.get('metric', 0)}" for r in data)))
    dns = runner.run('resolvectl', 'status', '--no-pager')
    if dns.ok:
        checks.append(Check('DNS', 'Resolver configuration available', details=dns.stdout.strip()))
    else:
        checks.append(unavailable('System resolver status', dns))
        try:
            checks.append(Check('DNS fallback', '/etc/resolv.conf', details=read_text('/etc/resolv.conf')))
        except OSError as exc:
            checks.append(Check('DNS fallback', 'Unavailable', Status.UNAVAILABLE, str(exc)))
    ports = runner.run('ss', '-H', '-lntu')
    checks.append(Check('Listening TCP / UDP ports', f'{len(ports.stdout.strip().splitlines())} listening sockets',
                        details=ports.stdout.strip() or 'No listeners reported') if ports.ok else unavailable('Listening ports', ports))
    gateway = next((r for r in routes if r.get('gateway')), None)
    if gateway:
        args = ['ping', '-n', '-c', '1', '-W', '2']
        if gateway.get('dev'):
            args.extend(['-I', gateway['dev']])
        args.append(gateway['gateway'])
        checks.append(reachability(runner, 'Gateway reachability', args))
    else:
        checks.append(Check('Gateway reachability', 'No gateway available to test', Status.UNAVAILABLE))
    checks.append(reachability(runner, 'Internet reachability', ['ping', '-n', '-c', '1', '-W', '2', '1.1.1.1']))
    checks.append(Check('Network probe scope', 'One ICMP echo to the gateway and 1.1.1.1', details=
                        'No report data is transmitted. These probes do not test DNS resolution or HTTPS; blocked ICMP is inconclusive.'))
    return checks


def reachability(runner, title, args):
    result = runner.run(*args, timeout=4)
    if result.ok:
        return Check(title, 'ICMP reply received', Status.OK, result.stdout.strip())
    if result.problem or result.code != 1:
        return unavailable(title, result)
    return Check(title, 'No ICMP reply · connectivity inconclusive', Status.WARNING,
                 result.reason + '\nICMP may be filtered; this does not prove an outage.')
