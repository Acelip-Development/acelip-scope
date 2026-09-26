"""Collector results shared by the CLI, reports, and GTK UI."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum


class Status(StrEnum):
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class Support(StrEnum):
    """Coverage is independent of health severity: unsupported is not a fault."""
    SUPPORTED = 'SUPPORTED'
    PARTIAL = 'PARTIAL'
    UNAVAILABLE = 'UNAVAILABLE'
    UNSUPPORTED = 'UNSUPPORTED'
    UNKNOWN = 'UNKNOWN'


@dataclass(frozen=True)
class Check:
    title: str
    summary: str
    status: Status = Status.INFO
    details: str = ""
    source: str = ""
    observed_at: datetime | None = None
    count: int | None = None
    support: Support | None = None
    remediation: dict | None = None

    def __post_init__(self):
        if self.support is None:
            object.__setattr__(self, 'support', Support.UNAVAILABLE if self.status == Status.UNAVAILABLE else Support.SUPPORTED)

    def to_dict(self):
        data = asdict(self)
        data['observed_at'] = self.observed_at.isoformat() if self.observed_at else None
        return data


@dataclass
class Snapshot:
    mode: str
    started: datetime
    sections: dict[str, list[Check]] = field(default_factory=dict)
    finished: datetime | None = None
    cancelled: bool = False

    def counts(self) -> dict[str, int]:
        return {s.value: sum(c.status == s for cs in self.sections.values() for c in cs)
                for s in Status}

    def to_dict(self) -> dict:
        return {"mode": self.mode, "started": self.started.isoformat(),
                "finished": self.finished.isoformat() if self.finished else None,
                "cancelled": self.cancelled, "counts": self.counts(),
                "sections": {name: [c.to_dict() for c in cs]
                             for name, cs in self.sections.items()}}


@dataclass(frozen=True)
class DistroInfo:
    id: str = 'unknown'
    name: str = 'Unknown Linux distribution'
    version: str = ''
    version_id: str = ''
    id_like: tuple[str, ...] = ()
    family: str = 'unknown'


@dataclass(frozen=True)
class DesktopInfo:
    environment: str = 'unknown'
    session_type: str = 'unknown'
    display_server: str = 'unknown'
    session_name: str = 'unknown'
    portal_backend: str = 'unknown'
    support: Support = Support.UNKNOWN


@dataclass(frozen=True)
class CommandCapability:
    name: str
    available: bool = False
    path: str | None = None
    version: str | None = None
    source: str = 'PATH'
    support: Support = Support.UNAVAILABLE


class ServiceStatus(StrEnum):
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    FAILED = 'FAILED'
    INACTIVE = 'INACTIVE'
    NOT_FOUND = 'NOT_FOUND'
    UNSUPPORTED = 'UNSUPPORTED'
    UNKNOWN = 'UNKNOWN'


@dataclass(frozen=True)
class ServiceState:
    name: str
    state: ServiceStatus = ServiceStatus.UNKNOWN
    scope: str = 'system'
    manager: str = 'unknown'
    support: Support = Support.UNKNOWN
    evidence: str = ''


@dataclass(frozen=True)
class PackageInfo:
    name: str
    version: str | None = None
    source: str = 'unknown'
    package_manager: str = 'unknown'
    install_path: str | None = None
    sandboxed: bool | None = None
    confidence: str = 'unknown'
    support: Support = Support.UNKNOWN
    installed: bool | None = None
    evidence: str = ''


@dataclass(frozen=True)
class SensorReading:
    chip: str
    label: str
    value: float
    unit: str
    kind: str
    source: str = ''
