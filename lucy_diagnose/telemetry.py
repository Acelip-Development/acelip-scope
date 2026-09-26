"""Platform-neutral live metric models and bounded in-memory history."""
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

METRICS = {'cpu': ('CPU', '%'), 'cpu_temp': ('CPU temperature', '°C'), 'ram': ('RAM', '%'),
           'gpu': ('GPU', '%'), 'gpu_temp': ('GPU temperature', '°C'), 'vram': ('VRAM', '%')}

@dataclass
class Sample:
    observed_at: datetime
    values: dict = field(default_factory=lambda: dict.fromkeys(METRICS))
    notes: dict = field(default_factory=dict)

class LiveHistory:
    def __init__(self, limit=60):
        self.samples = deque(maxlen=limit)

    def append(self, sample):
        self.samples.append(sample)
