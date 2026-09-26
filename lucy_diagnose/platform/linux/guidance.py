"""Explanation and manual read-only suggestions. This module cannot execute commands."""
from ...models import Status


def guidance_for(check, explanation='Review the scope and evidence before drawing a conclusion.'):
    if check.status not in {Status.WARNING, Status.ERROR}:
        return None
    title = check.title.lower()
    cause = 'The observation alone does not establish a root cause.'
    next_step = 'Review the evidence and original observation time, then repeat the relevant focused scan if needed.'
    commands = []
    if 'failed services' in title:
        cause = 'A unit exited unsuccessfully, or a previous failure remains recorded.'
        next_step = 'Identify the affected unit and inspect its status and journal before deciding whether any change is warranted.'
        commands = ['systemctl --failed --no-pager']
    elif 'journal' in title:
        cause = 'An application or service logged an error; it may be historical or transient.'
        next_step = 'Compare the event time and affected unit with the current symptoms. Journal visibility depends on your existing permissions.'
        commands = ['journalctl --priority=err --since="24 hours ago" --lines=100 --no-pager']
    elif title.startswith('disk ·') or 'filesystem' in title:
        cause = 'Files, caches, snapshots, or reserved blocks may be consuming capacity.'
        next_step = 'Inspect which filesystem is full and review its contents manually. Back up important data before deciding what to remove.'
        commands = ['df -hT']
    elif 'smart' in title:
        cause = 'The device reported a health condition or historical error. The exact SMART attributes need review.'
        next_step = 'Ensure important files are backed up and review the device vendor health guidance. LUCY will not run device tests or elevate permissions.'
    elif 'oom' in title:
        cause = 'Memory pressure or a process/container memory limit may have caused the kernel to terminate a process.'
        next_step = 'Match the event time to the affected process and inspect current memory and swap use.'
        commands = ['free -h']
    elif 'dpkg' in title:
        cause = 'An interrupted or incomplete package operation may have left an unconfigured package.'
        next_step = 'Inspect the audit output and consult Ubuntu package recovery guidance before performing any package changes.'
        commands = ['dpkg --audit']
    elif 'reachability' in title:
        cause = 'ICMP may be blocked, the route may be unavailable, or the peer may not reply.'
        next_step = 'Review the active interface and default route. An ICMP failure alone does not prove an internet outage.'
        commands = ['ip -json route show default']
    elif any(word in title for word in ('portal', 'pipewire', 'sharing', 'wireplumber')):
        cause = 'Portal/backend compatibility, session state, sandbox access, or a logged past fault may be involved.'
        next_step = 'Inspect the sharing service states, installed Discord source, and timestamps. Use Test Screen Sharing for an explicitly initiated manual attempt.'
        commands = ['systemctl --user show pipewire.service wireplumber.service xdg-desktop-portal.service --property=Id,LoadState,ActiveState,SubState --no-pager']
    elif any(word in title for word in ('gpu', 'nvidia', 'vram')):
        cause = 'Workload, cooling, or driver availability may affect the reading; thresholds are guides, not a hardware diagnosis.'
        next_step = 'Compare the observation with current GPU load and temperature. Do not change drivers based on this check alone.'
        commands = ['nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv']
    return {'what_happened': check.summary, 'why_it_matters': explanation,
            'evidence': check.details or check.summary, 'likely_cause': cause + ' This is a hypothesis.',
            'suggested_next_step': next_step, 'manual_read_only_commands': commands,
            'requires_sudo': False, 'automatic_execution': False}


def guidance_text(guidance):
    if not guidance:
        return ''
    lines = [f'{title}: {guidance[key]}' for key, title in
             (('what_happened', 'What happened'), ('why_it_matters', 'Why it matters'),
              ('likely_cause', 'Likely cause'), ('suggested_next_step', 'Suggested next step'))]
    if guidance['manual_read_only_commands']:
        lines.append('Manual read-only commands · not executed · no sudo required:\n' + '\n'.join(guidance['manual_read_only_commands']))
    return '\n\n'.join(lines)
