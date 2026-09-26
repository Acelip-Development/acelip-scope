from . import ai_stack, health, network, overview, sharing, storage
from .runner import Runner
from .telemetry import TelemetrySampler
from .sources import source_for
from .guidance import guidance_for


class LinuxPlatform:
    name = 'Linux'
    source_for = staticmethod(source_for)
    guidance_for = staticmethod(guidance_for)

    def create_runner(self, cancel=None, max_bytes=262144):
        return Runner(cancel, max_bytes)

    def create_sampler(self):
        return TelemetrySampler()

    def scan_jobs(self, mode):
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
