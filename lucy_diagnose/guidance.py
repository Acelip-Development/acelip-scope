"""Shared guidance presentation. Platform commands arrive as inert check metadata."""
from .models import Status


def guidance_for(check, explanation='Review the scope and evidence before drawing a conclusion.'):
    if check.status not in {Status.WARNING, Status.ERROR}:
        return None
    return check.remediation or {
        'what_happened': check.summary, 'why_it_matters': explanation,
        'evidence': check.details or check.summary,
        'likely_cause': 'The observation alone does not establish a root cause. Any explanation is a hypothesis.',
        'suggested_next_step': 'Review the source and timestamp, then repeat the relevant focused scan if needed.',
        'manual_read_only_commands': [], 'requires_sudo': False, 'automatic_execution': False}


def guidance_text(guidance):
    if not guidance:
        return ''
    lines = [f'{title}: {guidance[key]}' for key, title in
             (('what_happened', 'What happened'), ('why_it_matters', 'Why it matters'),
              ('likely_cause', 'Likely cause'), ('suggested_next_step', 'Suggested next step'))]
    if guidance['manual_read_only_commands']:
        lines.append('Manual read-only commands · not executed · no sudo required:\n' + '\n'.join(guidance['manual_read_only_commands']))
    return '\n\n'.join(lines)
