"""Pure report preparation. Produces copies; never writes files or sends data."""
from .identity import DISPLAY_NAME, PUBLISHER, EXECUTABLE_NAME
from datetime import datetime
import json
import re

from . import __version__
from .dashboard import SUBSYSTEMS
from .privacy import PrivacyContext, redact_secrets, sanitize_report


def filter_copy(value, sanitize, context):
    if isinstance(value, str):
        return sanitize_report(value, context) if sanitize else redact_secrets(value)
    if isinstance(value, dict):
        return {key: filter_copy(item, sanitize, context) for key, item in value.items()}
    if isinstance(value, list):
        return [filter_copy(item, sanitize, context) for item in value]
    return value


def export_document(state, privacy='sanitized', context=None, now=None):
    context = context or PrivacyContext.current()
    now = now or datetime.now().astimezone()
    findings = []
    for finding in state.findings():
        check = finding.check
        findings.append({'subsystem': finding.subsystem, 'title': check.title, 'summary': check.summary,
                         'support': check.support.value,
                         'severity': check.status.value, 'explanation': finding.explanation,
                         'evidence': check.details or check.summary, 'source': check.source,
                         'observed_at': check.observed_at.isoformat() if check.observed_at else None,
                         'count': check.count, 'guidance': finding.guidance})
    host_titles = {'Ubuntu version', 'Operating system', 'Kernel', 'CPU model', 'GPU', 'NVIDIA GPU'}
    version_titles = {'Codex', 'Claude', 'Gemini', 'Opencode', 'NVIDIA driver', 'CUDA compatibility', 'Ollama API',
                      'Discord deb', 'Discord Snap', 'Discord Flatpak'}
    document = {'schema_version': 1, 'generated_at': now.isoformat(),
                'privacy': 'local-details-secrets-removed' if privacy == 'local' else 'sanitized',
                'host_summary': [{'title': f['title'], 'summary': f['summary']} for f in findings if f['title'] in host_titles],
                'scan_types_performed': sorted(state.scan_types),
                'latest_scan_cancelled': state.latest.cancelled if state.latest else None,
                'subsystem_status': {name: {'severity': state.status(name)[0].value, 'summary': state.status(name)[1]} for name in SUBSYSTEMS},
                'severity_counts': state.counts(), 'findings': findings,
                'screen_sharing': [f for f in findings if f['subsystem'] == 'Discord / Screen Sharing'],
                'tool_versions': [{'title': f['title'], 'summary': f['summary']} for f in findings if f['title'] in version_titles],
                'limitations': 'Current observations only; focused scans retain original timestamps. No graph history. '
                               'Screen-sharing prerequisites and user-reported manual outcomes do not constitute automated capture validation. '
                               'Redaction is best effort; review the preview before sharing.'}
    document = filter_copy(document, privacy != 'local', context)
    # Stable product metadata is not host identity (even if the hostname matches the product).
    document['app'] = {'name': DISPLAY_NAME, 'version': __version__, 'publisher': PUBLISHER}
    return document


def fenced(value):
    # Untrusted log text cannot close the evidence fence.
    fence = '`' * max(3, 1 + max((len(x) for x in re.findall(r'`+', str(value))), default=0))
    return f'{fence}text\n{value}\n{fence}'


def heading(value):
    return re.sub(r'([\\`*_{}\[\]<>#|])', r'\\\1', str(value).replace('\n', ' '))


def render_markdown(document):
    lines = [f"# {DISPLAY_NAME} {document['app']['version']}",
             f"Generated: {document['generated_at']} · Privacy: {document['privacy']}",
             'Scans: ' + ', '.join(document['scan_types_performed']),
             f"Latest scan cancelled: {document['latest_scan_cancelled']}",
             '## Host summary', *[f"- {heading(item['title'])}: {heading(item['summary'])}" for item in document['host_summary']],
             '## Subsystem status', *[f"- {name}: {data['severity'].upper()} · {data['summary']}" for name, data in document['subsystem_status'].items()],
             '## Counts', ', '.join(f'{key}: {value}' for key, value in document['severity_counts'].items()),
             '## Tool versions', *[f"- {heading(item['title'])}: {heading(item['summary'])}" for item in document['tool_versions']],
             '## Findings']
    for finding in document['findings']:
        lines.extend([f"### {finding['severity'].upper()} · {heading(finding['title'])}",
                      heading(finding['summary']), heading(finding['explanation']),
                      f"Subsystem: {finding['subsystem']} · Coverage: {finding['support']} · Source: {heading(finding['source'])} · Observed: {finding['observed_at']}",
                      'Evidence:', fenced(finding['evidence'])])
        if finding['guidance']:
            for key, value in finding['guidance'].items():
                if isinstance(value, str) and key != 'evidence':
                    lines.append(f"{key.replace('_', ' ').capitalize()}: {heading(value)}")
            if finding['guidance']['manual_read_only_commands']:
                lines.extend(['Manual read-only commands (never executed; no sudo required):', fenced('\n'.join(finding['guidance']['manual_read_only_commands']))])
    lines.extend(['## Scope and limitations', document['limitations']])
    return '\n\n'.join(lines) + '\n'


def prepare_export(state, format='markdown', privacy='sanitized', context=None):
    if format not in {'markdown', 'json'}:
        raise ValueError('Unsupported export format')
    document = export_document(state, privacy, context)
    text = json.dumps(document, indent=2, ensure_ascii=False) + '\n' if format == 'json' else render_markdown(document)
    stamp = datetime.fromisoformat(document['generated_at']).strftime('%Y-%m-%d-%H%M%S')
    return text, f'{EXECUTABLE_NAME}-{stamp}.{"json" if format == "json" else "md"}'
