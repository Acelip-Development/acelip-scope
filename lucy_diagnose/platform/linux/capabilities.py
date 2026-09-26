"""Command discovery does not execute commands unless a known version probe is requested."""
import shutil
from ...models import CommandCapability, Support

VERSION_ARGS = {name: ('--version',) for name in ('smartctl', 'sensors', 'wpctl', 'systemctl', 'flatpak',
                'rpm', 'pacman', 'dpkg-query', 'codex', 'claude', 'gemini', 'opencode')}


class Capabilities:
    def __init__(self, which=None):
        self.which = which

    def find_command(self, name, runner=None, version=False):
        from .sandbox import restricted, HOST_COMMANDS, RESTRICTION
        if restricted() and name.rsplit("/", 1)[-1] in HOST_COMMANDS:
            return CommandCapability(name, source=RESTRICTION, support=Support.UNAVAILABLE)
        try:
            path = (self.which or shutil.which)(name)
        except (OSError, ValueError):
            path = None
        if not path:
            return CommandCapability(name)
        if not version:
            return CommandCapability(name, True, path, support=Support.SUPPORTED)
        args = VERSION_ARGS.get(name)
        if runner is None or args is None:
            return CommandCapability(name, True, path, support=Support.PARTIAL)
        result = runner.run(path, *args, timeout=2)
        text = (result.stdout or result.stderr).strip().splitlines()
        value = text[0][:200] if result.ok and text else None
        return CommandCapability(name, True, path, value, support=Support.SUPPORTED if value else Support.PARTIAL)
