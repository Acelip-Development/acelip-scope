"""Guard actual dependency and execution boundaries, not cosmetic file layout."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'lucy_diagnose'
LINUX = ROOT / 'platform/linux'
OS_COMMANDS = {'systemctl', 'journalctl', 'lspci', 'lsblk', 'ip', 'nmcli', 'sensors', 'smartctl',
               'wpctl', 'pactl', 'loginctl', 'flatpak', 'snap', 'dpkg', 'rpm', 'pacman', 'zypper', 'nvidia-smi'}


class ArchitectureTests(unittest.TestCase):
    def test_only_linux_backend_imports_subprocess_for_diagnostics(self):
        for path in ROOT.rglob('*.py'):
            if path.is_relative_to(LINUX):
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertNotIn('subprocess', [alias.name for alias in node.names], str(path))
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, 'subprocess', str(path))

    def test_linux_paths_and_command_invocation_confined_to_backend(self):
        for path in ROOT.rglob('*.py'):
            if path.is_relative_to(LINUX):
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertFalse(node.value.startswith(('/proc/', '/sys/')), str(path))
                if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
                    if isinstance(node.func, ast.Attribute) and node.func.attr in {'run', 'Popen', 'call', 'check_output'}:
                        self.assertNotIn(node.args[0].value, OS_COMMANDS, str(path))

    def test_shared_modules_do_not_import_linux_probes(self):
        for path in [*ROOT.glob('*.py'), *(ROOT / 'ui').glob('*.py')]:
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse('platform.linux' in (node.module or ''), str(path))

    def test_placeholder_factory_imports_no_linux_dependencies_in_fresh_process(self):
        code = "from lucy_diagnose.platform.detect import get_platform; import sys; [get_platform(n) for n in ('Windows','Darwin','FreeBSD')]; assert not any(n.startswith('lucy_diagnose.platform.linux') for n in sys.modules)"
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT.parent, timeout=5,
                                capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_shell_true_or_unbounded_direct_process_calls_added(self):
        processes = []
        for path in ROOT.rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call):
                    self.assertFalse(any(k.arg == 'shell' and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords), str(path))
                    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess':
                        processes.append((path.relative_to(ROOT).as_posix(), node.func.attr))
        self.assertEqual(processes, [('platform/linux/runner.py', 'Popen')])
