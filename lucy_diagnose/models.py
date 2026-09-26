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


@dataclass(frozen=True)
class Check:
    title: str
    summary: str
    status: Status = Status.INFO
    details: str = ""
    source: str = ""
    observed_at: datetime | None = None
    count: int | None = None

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
