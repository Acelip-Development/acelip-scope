from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dataclasses import replace
import logging

from .collectors import ai_stack, health, network, overview, sharing, storage
from .models import Check, Snapshot, Status
from .runner import Runner
from .sources import source_for

MODES = ('Quick Scan', 'Full Scan', 'GPU', 'Network', 'Storage', 'AI Stack', 'Discord / Screen Sharing')
SECTION_ORDER = ('Overview', 'Health', 'Storage', 'Network', 'AI Stack', 'Discord / Screen Sharing')


def scan(mode='Quick Scan', runner=None, progress=None):
    if mode not in MODES:
        raise ValueError(f'Unknown diagnostic mode: {mode}')
    runner = runner or Runner()
    snapshot = Snapshot(mode, datetime.now().astimezone())
    jobs = {'Overview': overview.collect, 'Health': lambda r: health.collect(r, full=mode == 'Full Scan')}
    if mode == 'Full Scan':
        jobs.update({'Storage': storage.collect, 'Network': network.collect, 'AI Stack': ai_stack.collect,
                     'Discord / Screen Sharing': sharing.collect})
    elif mode != 'Quick Scan':
        section, collector = {'GPU': ('Overview', overview.collect_gpu), 'Network': ('Network', network.collect),
                              'Storage': ('Storage', storage.collect), 'AI Stack': ('AI Stack', ai_stack.collect),
                              'Discord / Screen Sharing': ('Discord / Screen Sharing', sharing.collect)}[mode]
        jobs = {section: collector}
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
            snapshot.sections[name] = [replace(c, source=c.source or source_for(name, c.title),
                                               observed_at=c.observed_at or observed) for c in snapshot.sections[name]]
            if progress:
                progress(name, len(snapshot.sections), len(jobs))
    snapshot.sections = {name: snapshot.sections[name] for name in SECTION_ORDER if name in snapshot.sections}
    snapshot.cancelled = runner.cancel.is_set()
    snapshot.finished = datetime.now().astimezone()
    return snapshot
