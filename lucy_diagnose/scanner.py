from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dataclasses import replace
import logging

from .models import Check, Snapshot, Status
from .platform.detect import get_platform

MODES = ('Quick Scan', 'Full Scan', 'GPU', 'Network', 'Storage', 'AI Stack', 'Discord / Screen Sharing')
SECTION_ORDER = ('Overview', 'Health', 'Storage', 'Network', 'AI Stack', 'Discord / Screen Sharing')


def scan(mode='Quick Scan', runner=None, progress=None, platform=None):
    if mode not in MODES:
        raise ValueError(f'Unknown diagnostic mode: {mode}')
    platform = platform or get_platform()
    runner = runner or platform.create_runner()
    snapshot = Snapshot(mode, datetime.now().astimezone())
    jobs = platform.scan_jobs(mode)
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix='lucy-collector') as executor:
        futures = {executor.submit(fn, runner): name for name, fn in jobs.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                snapshot.sections[name] = future.result()
            except Exception as exc:
                logging.getLogger(__name__).error('Collector failed: %s (%s)', name, type(exc).__name__)
                snapshot.sections[name] = [Check(name, 'Collector failed; see project log', Status.UNAVAILABLE)]
            observed = datetime.now().astimezone()
            snapshot.sections[name] = [replace(c, source=c.source or platform.source_for(name, c.title),
                                               observed_at=c.observed_at or observed,
                                               remediation=c.remediation or platform.guidance_for(c)) for c in snapshot.sections[name]]
            if progress:
                progress(name, len(snapshot.sections), len(jobs))
    snapshot.sections = {name: snapshot.sections[name] for name in SECTION_ORDER if name in snapshot.sections}
    snapshot.cancelled = runner.cancel.is_set()
    snapshot.finished = datetime.now().astimezone()
    return snapshot
