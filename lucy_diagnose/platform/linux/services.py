"""Read-only service queries; absence of systemd is an unsupported capability."""
from pathlib import Path
import re
from .capabilities import Capabilities
from .runner import Runner
from ...models import Check, ServiceState, ServiceStatus, Status, Support


def parse_units(text):
    return {fields['Id']: fields for block in text.strip().split('\n\n')
            if (fields := dict(line.split('=', 1) for line in block.splitlines() if '=' in line)) and 'Id' in fields}


def normalize_service(name, data, scope='system'):
    if data.get('LoadState') == 'not-found':
        state = ServiceStatus.NOT_FOUND
    else:
        state = {'active': ServiceStatus.RUNNING, 'failed': ServiceStatus.FAILED,
                 'inactive': ServiceStatus.STOPPED if data.get('SubState') == 'dead' else ServiceStatus.INACTIVE}.get(data.get('ActiveState'), ServiceStatus.UNKNOWN)
    return ServiceState(name, state, scope, 'systemd', Support.SUPPORTED if state != ServiceStatus.UNKNOWN else Support.UNKNOWN,
                        '\n'.join(f'{key}={value}' for key, value in data.items()))


class Services:
    def __init__(self, capabilities=None, systemd_present=None):
        self.capabilities = capabilities or Capabilities()
        self._present = systemd_present

    @property
    def supported(self):
        present = self._present if self._present is not None else Path('/run/systemd/system').is_dir()
        return present and self.capabilities.find_command('systemctl').available

    def get_many(self, names, scope='system', runner=None):
        if scope not in {'system', 'user'} or any(not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.@:\\-]*', name) for name in names):
            raise ValueError('Invalid service name or scope')
        if not names:
            return []
        from .sandbox import restricted, RESTRICTION
        if restricted():
            return [ServiceState(name, scope=scope, support=Support.UNAVAILABLE, evidence=RESTRICTION) for name in names]
        if not self.supported:
            return [ServiceState(name, ServiceStatus.UNSUPPORTED, scope, support=Support.UNSUPPORTED,
                                 evidence='No supported running service manager detected') for name in names]
        runner = runner or Runner()
        args = ('--user',) if scope == 'user' else ()
        result = runner.run('systemctl', *args, 'show', *names, '--property=Id,Names,LoadState,ActiveState,SubState', '--no-pager')
        if not result.ok:
            return [ServiceState(name, scope=scope, manager='systemd', support=Support.UNAVAILABLE, evidence=result.reason) for name in names]
        data = parse_units(result.stdout)
        # systemctl resolves aliases to a canonical Id (for example gdm.service
        # for display-manager.service). Never depend on positional output order.
        for fields in tuple(data.values()):
            for alias in fields.get('Names', '').split():
                data.setdefault(alias, fields)
        return [normalize_service(name, data.get(name, {}), scope) for name in names]

    def get(self, name, scope='system', runner=None):
        return self.get_many((name,), scope, runner)[0]

    def process(self, name, runner=None):
        result = (runner or Runner()).run('ps', '-eo', 'comm=')
        if not result.ok:
            return ServiceState(name, scope='process', manager='process-only', support=Support.UNAVAILABLE, evidence=result.reason)
        found = name.casefold() in {line.strip().casefold() for line in result.stdout.splitlines()}
        return ServiceState(name, ServiceStatus.RUNNING if found else ServiceStatus.NOT_FOUND, 'process', 'process-only',
                            Support.PARTIAL, 'Process-name observation only; not a service health check')


def service_check(service, title=None):
    status = Status.ERROR if service.state == ServiceStatus.FAILED else Status.OK if service.state == ServiceStatus.RUNNING else Status.INFO
    if service.support in {Support.UNSUPPORTED, Support.UNAVAILABLE, Support.UNKNOWN} or service.state == ServiceStatus.NOT_FOUND:
        status = Status.UNAVAILABLE
    return Check(title or service.name, service.state.value, status,
                 f'{service.scope} · {service.manager}\n{service.evidence}\nInactive on-demand services are not necessarily faults. No activation attempted.',
                 source=f'{service.manager} · {service.scope} service query',
                 support=Support.UNAVAILABLE if service.state == ServiceStatus.NOT_FOUND else service.support)
