from . import ai_stack, health, network, overview, sharing, storage
from .runner import Runner
from .telemetry import TelemetrySampler
from .sources import source_for
from .guidance import guidance_for
from .capabilities import Capabilities
from .packages import Packages
from .services import Services
from .distro import detect_distro
from .desktop import detect_desktop, configure_ui_environment, owned_portal_backends, backend_for_desktop
from .sensors import sensor_status
from .analysis_commands import analysis_command


class LinuxPlatform:
    name = 'Linux'
    source_for = staticmethod(source_for)
    guidance_for = staticmethod(guidance_for)
    analysis_command = staticmethod(analysis_command)
    configure_ui_environment = staticmethod(configure_ui_environment)

    def __init__(self):
        self.capabilities = Capabilities()
        self.packages = Packages(capabilities=self.capabilities)
        self.services = Services(self.capabilities)

    def get_distro_info(self):
        return detect_distro()

    def get_desktop_info(self, runner=None):
        desktop = detect_desktop()
        backend = backend_for_desktop(desktop.environment, owned_portal_backends(runner or self.create_runner()))
        return detect_desktop(portal_backend=backend)

    def get_service_status(self, name, scope='system', runner=None):
        return self.services.get(name, scope, runner)

    def get_package_info(self, name, runner=None):
        return self.packages.find(name, runner)

    def get_sensor_status(self, runner=None):
        readings, support = sensor_status(runner or self.create_runner())
        from .sandbox import restricted
        from ...models import Support
        return readings, Support.PARTIAL if restricted() and readings else support

    def create_runner(self, cancel=None, max_bytes=262144):
        return Runner(cancel, max_bytes)

    def create_sampler(self):
        return TelemetrySampler()

    def scan_jobs(self, mode):
        from . import sandbox
        if sandbox.restricted():
            from ..base import SCOPES
            return {section: lambda runner, section=section: sandbox.collect(section, runner) for section in SCOPES[mode]}
        if mode in {'Quick Scan', 'Full Scan'}:
            jobs = {'Overview': overview.collect, 'Health': lambda r: health.collect(r, full=mode == 'Full Scan')}
            if mode == 'Full Scan':
                jobs.update({'Storage': storage.collect, 'Network': network.collect, 'AI Stack': ai_stack.collect,
                             'Discord / Screen Sharing': sharing.collect})
            return jobs
        section, collector = {'GPU': ('Overview', overview.collect_gpu), 'Network': ('Network', network.collect),
                              'Storage': ('Storage', storage.collect), 'AI Stack': ('AI Stack', ai_stack.collect),
                              'Discord / Screen Sharing': ('Discord / Screen Sharing', sharing.collect)}[mode]
        return {section: collector}
