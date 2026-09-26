"""Audio observation with independent sources; never starts an audio service."""
import os

from ...models import Check, ServiceStatus, Status, Support
from .capabilities import Capabilities


def audio_capabilities(runner, services, states, capabilities=None, runtime=None):
    capabilities = capabilities or Capabilities()
    runtime = runtime if runtime is not None else os.environ.get('XDG_RUNTIME_DIR')
    running = {state.name for state in states if state.state == ServiceStatus.RUNNING}
    # Process-only evidence also works without a systemd user bus. It cannot
    # establish service health, so retain partial coverage unless a client replies.
    pipewire = 'pipewire.service' in running or services.process('pipewire', runner).state == ServiceStatus.RUNNING
    pulse = 'pipewire-pulse.service' in running or services.process('pulseaudio', runner).state == ServiceStatus.RUNNING
    evidence, responsive = [], []
    for command in ('wpctl', 'pactl'):
        present = capabilities.find_command(command).available
        evidence.append(f'{command}: {"available" if present else "unavailable"}')
        # Do not contact a dormant socket: optional clients must not activate a
        # service. An explicit Pulse server path also avoids autospawn/discovery.
        if command == 'wpctl' and present and pipewire:
            args = ('wpctl', 'status')
        elif command == 'pactl' and present and pulse and runtime:
            args = ('pactl', '--server=unix:' + runtime + '/pulse/native', 'info')
        else:
            continue
        result = runner.run(*args, timeout=4)
        valid = ('PipeWire' in result.stdout and 'Audio' in result.stdout if command == 'wpctl' else
                 any(line.startswith('Server Name:') for line in result.stdout.splitlines()))
        if result.ok and valid:
            responsive.append(command)
            evidence.append(result.stdout.strip())
        else:
            evidence.append(f'{command}: {result.reason}')
    support = Support.SUPPORTED if responsive else Support.PARTIAL if pipewire or pulse else Support.UNAVAILABLE
    summary = ('Audio metadata available via ' + ', '.join(responsive) if responsive else
               'Audio process/service observed; client metadata unavailable' if pipewire or pulse else
               'No running audio server established')
    evidence.append('Metadata only; playback, microphone and capture audio remain unverified. No service activation requested.')
    return Check('Audio capabilities', summary, Status.INFO if support != Support.UNAVAILABLE else Status.UNAVAILABLE,
                 '\n'.join(evidence), source='Linux audio services/processes and optional read-only clients', support=support)
