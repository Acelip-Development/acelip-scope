"""Shared platform contract and safe unsupported fallback; never imports Linux."""
from datetime import datetime
import threading
from typing import Callable, Protocol, runtime_checkable

from ..commands import Result
from ..models import Check, CommandCapability, DesktopInfo, DistroInfo, PackageInfo, SensorReading, ServiceState, ServiceStatus, Status, Support
from ..telemetry import METRICS, Sample

SCOPES = {'Quick Scan': ('Overview', 'Health'),
          'Full Scan': ('Overview', 'Health', 'Storage', 'Network', 'AI Stack', 'Discord / Screen Sharing'),
          'GPU': ('Overview',), 'Network': ('Network',), 'Storage': ('Storage',),
          'AI Stack': ('AI Stack',), 'Discord / Screen Sharing': ('Discord / Screen Sharing',)}


class CommandRunner(Protocol):
    cancel: threading.Event
    def run(self, *argv: str, timeout: float = 7) -> Result: ...


class PackageQueries(Protocol):
    def find(self, name: str, runner: CommandRunner | None = None) -> list[PackageInfo]: ...


class CommandCapabilities(Protocol):
    def find_command(self, name: str, runner: CommandRunner | None = None, version: bool = False) -> CommandCapability: ...


class MetricSampler(Protocol):
    def sample(self, runner: CommandRunner, epoch=None) -> Sample: ...


@runtime_checkable
class Platform(Protocol):
    name: str
    packages: PackageQueries
    capabilities: CommandCapabilities
    def scan_jobs(self, mode: str) -> dict[str, Callable[[CommandRunner], list[Check]]]: ...
    def create_runner(self, cancel=None, max_bytes=262144) -> CommandRunner: ...
    def create_sampler(self) -> MetricSampler: ...
    def get_desktop_info(self, runner=None) -> DesktopInfo: ...
    def get_distro_info(self) -> DistroInfo: ...
    def get_service_status(self, name: str, scope='system', runner=None) -> ServiceState: ...
    def get_package_info(self, name: str, runner=None) -> list[PackageInfo]: ...
    def get_sensor_status(self, runner=None) -> tuple[list[SensorReading], Support]: ...
    def source_for(self, section: str, title: str) -> str: ...
    def guidance_for(self, check: Check): ...
    def analysis_command(self, provider: str, model: str) -> str: ...
    def configure_ui_environment(self, project): ...


class UnsupportedRunner:
    def __init__(self, cancel=None, **_):
        self.cancel = cancel or threading.Event()

    def run(self, *argv, timeout=7):
        return Result(tuple(argv), problem='Platform diagnostics UNSUPPORTED')


class UnsupportedSampler:
    def sample(self, runner, epoch=None):
        return Sample(datetime.now().astimezone(), notes={key: 'UNSUPPORTED on this platform' for key in METRICS})


class UnsupportedCapabilities:
    def find_command(self, name, **_):
        return CommandCapability(name, source='Unsupported platform', support=Support.UNSUPPORTED)


class UnsupportedPackages:
    def find(self, name, **_):
        return [PackageInfo(name, support=Support.UNSUPPORTED, evidence='Package inspection unsupported on this platform')]


class UnsupportedPlatform:
    name = 'Unsupported'
    capabilities = UnsupportedCapabilities()
    packages = UnsupportedPackages()

    def scan_jobs(self, mode):
        return {section: lambda runner, s=section: [Check(s, f'{self.name} diagnostics are not implemented',
                Status.UNAVAILABLE, source=self.name + ' backend', support=Support.UNSUPPORTED)] for section in SCOPES[mode]}

    def create_runner(self, cancel=None, max_bytes=262144):
        return UnsupportedRunner(cancel)

    def create_sampler(self):
        return UnsupportedSampler()

    def get_desktop_info(self, runner=None):
        return DesktopInfo(support=Support.UNSUPPORTED)

    def get_distro_info(self):
        return DistroInfo()

    def get_service_status(self, name, scope='system', runner=None):
        return ServiceState(name, ServiceStatus.UNSUPPORTED, scope, support=Support.UNSUPPORTED)

    def get_package_info(self, name, runner=None):
        return self.packages.find(name)

    def get_sensor_status(self, runner=None):
        return [], Support.UNSUPPORTED

    def source_for(self, section, title):
        return self.name + ' backend'

    def guidance_for(self, check):
        return None

    def analysis_command(self, provider, model):
        raise ValueError(f'AI command handoff is UNSUPPORTED on {self.name}')

    def configure_ui_environment(self, project):
        pass
