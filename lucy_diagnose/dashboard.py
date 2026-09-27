"""Current dashboard state, with scoped replacement instead of scan history."""

from dataclasses import dataclass, replace
from datetime import datetime

from .models import Check, Snapshot, Status, Support
from .sources import source_for
from .guidance import guidance_for, guidance_text

SUBSYSTEMS = ('System', 'GPU / NVIDIA', 'Network', 'Storage', 'AI Stack', 'Discord / Screen Sharing')
GROUP_SUBSYSTEM = {'system': 'System', 'health': 'System', 'gpu': 'GPU / NVIDIA', 'capacity': 'Storage',
                   'storage': 'Storage', 'network': 'Network', 'ai': 'AI Stack', 'sharing': 'Discord / Screen Sharing'}
SCOPES = {'Quick Scan': ('system', 'health', 'gpu', 'capacity'), 'Full Scan': tuple(GROUP_SUBSYSTEM),
          'GPU': ('gpu',), 'Network': ('network',), 'Storage': ('capacity', 'storage'),
          'AI Stack': ('ai',), 'Discord / Screen Sharing': ('sharing',)}
RANK = {Status.ERROR: 0, Status.WARNING: 1, Status.INFO: 2, Status.UNAVAILABLE: 3, Status.OK: 4}

SEVERITIES = ('Attention', 'All findings', 'Critical', 'Warnings', 'Info', 'Unavailable', 'Passed')
SEVERITY_FILTERS = ({Status.ERROR, Status.WARNING}, set(Status), {Status.ERROR},
                    {Status.WARNING}, {Status.INFO}, {Status.UNAVAILABLE}, {Status.OK})


def finding_key(finding):
    return finding.subsystem, finding.check.title, finding.check.source


def is_capacity(check):
    return check.title.startswith('Disk ·') or check.title == 'Filesystem usage'


def is_gpu(check):
    return any(word in check.title for word in ('GPU', 'NVIDIA', 'CUDA', 'VRAM'))


@dataclass(frozen=True)
class Finding:
    subsystem: str
    check: Check

    @property
    def guidance(self):
        return guidance_for(self.check, self.explanation)

    @property
    def explanation(self):
        c = self.check
        if c.support == Support.UNSUPPORTED:
            return 'The selected platform backend does not implement this check. This is a coverage limitation, not a system fault.'
        if c.status == Status.UNAVAILABLE:
            return 'This check could not establish a result. Missing tools, restricted access, or a timeout do not prove a system fault.'
        if c.title == 'Failed services / units' and c.status == Status.ERROR:
            return 'The service manager reports unsuccessful units. The evidence identifies which units need review; no service was restarted or changed.'
        if 'journal errors' in c.title.lower() and c.status == Status.WARNING:
            return 'Error-level journal entries were found in the stated time window. They can describe past events and do not by themselves prove a current outage.'
        if c.title.startswith('Disk ·') and c.status in {Status.WARNING, Status.ERROR}:
            return 'Filesystem usage crossed the configured capacity threshold: warning at 85%, critical at 95%.'
        if c.title.startswith('SMART ·') and c.status in {Status.WARNING, Status.ERROR}:
            return 'The device reported a health or history condition that needs review. No self-test or device change was performed.'
        if 'reachability' in c.title.lower():
            return 'This is a single ICMP probe. A missing reply can mean filtering, and a successful reply does not verify DNS or HTTPS.'
        if c.status == Status.OK:
            return 'This read-only check completed without reporting a problem within its stated scope.'
        return 'An observation from the stated source and time. Review its scope and evidence before drawing a broader conclusion.'

    @property
    def text(self):
        c = self.check
        return (f'{c.status.value.upper()} · {self.subsystem} · {c.title}\n{c.summary}\nExplanation: {self.explanation}\n'
                f'Coverage: {c.support.value}\nSource: {c.source}\nObserved: {c.observed_at.isoformat(timespec="seconds") if c.observed_at else "Unknown"}\n'
                f'Evidence:\n{c.details or c.summary}\n\n{guidance_text(self.guidance)}')


class DashboardState:
    def __init__(self):
        self.groups = {}
        self.latest = None
        self.manual_sharing = None
        self.scan_types = set()

    def merge(self, snapshot):
        self.scan_types.add(snapshot.mode)
        incoming = {group: [] for group in SCOPES[snapshot.mode]}
        for section, checks in snapshot.sections.items():
            for check in checks:
                c = replace(check, source=check.source or source_for(section, check.title),
                            observed_at=check.observed_at or snapshot.finished or snapshot.started)
                if section == 'Overview':
                    group = 'gpu' if snapshot.mode == 'GPU' or is_gpu(c) else 'capacity' if is_capacity(c) else 'system'
                elif section == 'Health':
                    if is_capacity(c):
                        continue  # Capacity is already collected by Overview/Storage.
                    group = 'health'
                elif section == 'Storage':
                    group = 'capacity' if is_capacity(c) else 'storage'
                else:
                    group = {'Network': 'network', 'AI Stack': 'ai', 'Discord / Screen Sharing': 'sharing'}[section]
                incoming.setdefault(group, []).append(c)
        for group, checks in incoming.items():
            # Replacing a scope also removes resolved findings. Never discard other scopes.
            if not checks:
                checks = [Check(GROUP_SUBSYSTEM[group], 'No results available for this scan scope', Status.UNAVAILABLE,
                                'The scan may have been cancelled or its collector failed.', source=f'{group} collector',
                                observed_at=snapshot.finished or snapshot.started)]
            unique = {}
            for c in checks:
                key = (c.title, c.source)
                if key not in unique or c.observed_at >= unique[key].observed_at:
                    unique[key] = c
            self.groups[group] = list(unique.values())
        self.latest = snapshot

    def findings(self, subsystem=None):
        items = []
        if self.manual_sharing and subsystem in (None, 'Discord / Screen Sharing'):
            items.append(Finding('Discord / Screen Sharing', self.manual_sharing))
        seen = set()
        for group, checks in self.groups.items():
            name = GROUP_SUBSYSTEM[group]
            if subsystem and subsystem != name:
                continue
            for check in checks:
                key = (name, check.title, check.source)
                if key not in seen:
                    items.append(Finding(name, check))
                    seen.add(key)
        return sorted(items, key=lambda f: (RANK[f.check.status], f.subsystem, f.check.title))

    def filtered_findings(self, severity=0, subsystem=None):
        """Presentation filters never mutate observations or their timestamps."""
        return [f for f in self.findings(subsystem) if f.check.status in SEVERITY_FILTERS[severity]]

    def attention_preview(self):
        return self.filtered_findings()[:3]

    def subsystem_summary(self, name, compact=False):
        """Presentation only: one compact fact or two detail-context summary lines."""
        items = self.findings(name)
        if not items:
            return 'No observations' if compact else 'Run a scan to check this subsystem'
        unavailable = sum(f.check.status == Status.UNAVAILABLE for f in items)
        attention = sum(f.check.status in {Status.ERROR, Status.WARNING} for f in items)
        counts = []
        if attention:
            counts.append(f'{attention} need attention')
        if unavailable and not compact:
            counts.append(f'{unavailable} unavailable')
        if not counts:
            counts.append(f'{len(items)} check{"s" if len(items) != 1 else ""} observed')
        restricted = any('Flatpak' in f.check.summary and f.check.status == Status.UNAVAILABLE for f in items)
        fact = 'Flatpak host access restricted' if restricted and not compact else ''
        cooling = self.find('Cooling telemetry') if name == 'System' else None
        if cooling and cooling.status != Status.UNAVAILABLE:
            fact = 'Cooling: ' + cooling.summary.replace(' cooling readings', ' readings')
        elif name == 'Storage' and (compact or not restricted):
            percents = []
            for f in items:
                if f.check.title.startswith('Disk ·'):
                    try:
                        percents.append(float(f.check.summary.split('%')[0]))
                    except ValueError:
                        pass
            if percents:
                fact = f'{max(percents):g}% busiest filesystem'
        elif name == 'Discord / Screen Sharing' and not restricted and not compact:
            fact = 'Manual sharing test available'
        if compact:
            return ' · '.join(part for part in (fact, counts[0] if attention or not fact else '') if part)
        return '\n'.join(part for part in (fact, ' · '.join(counts)) if part)

    def counts(self):
        return {s.value: sum(f.check.status == s for f in self.findings()) for s in Status}

    def status(self, subsystem=None):
        items = self.findings(subsystem)
        groups = [g for g, name in GROUP_SUBSYSTEM.items() if not subsystem or subsystem == name]
        statuses = {f.check.status for f in items}
        if Status.ERROR in statuses:
            return Status.ERROR, 'Critical findings'
        if Status.WARNING in statuses:
            return Status.WARNING, 'Needs attention'
        if not items:
            return Status.UNAVAILABLE, 'Not checked yet'
        if Status.UNAVAILABLE in statuses or any(f.check.support != Support.SUPPORTED for f in items) or any(g not in self.groups for g in groups):
            return Status.UNAVAILABLE, 'Incomplete coverage'
        return Status.OK, 'No issues detected'

    def find(self, title):
        return next((f.check for f in self.findings() if f.check.title == title), None)

    def snapshot(self):
        now = datetime.now().astimezone()
        items = self.findings()
        return Snapshot('Unified dashboard · latest ' + (self.latest.mode if self.latest else 'no scan'),
                        min((f.check.observed_at for f in items if f.check.observed_at), default=now),
                        {name: [f.check for f in items if f.subsystem == name] for name in SUBSYSTEMS},
                        self.latest.finished if self.latest else now,
                        self.latest.cancelled if self.latest else False)
