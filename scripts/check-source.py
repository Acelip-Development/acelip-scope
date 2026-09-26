#!/usr/bin/env python3
"""Fast syntax checks without importing application code or writing bytecode."""
import ast
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
for name in filter(None, paths):
    path = root / name
    if path.suffix == '.py':
        ast.parse(path.read_text(), filename=name)
    elif path.suffix == '.sh':
        subprocess.run(['sh', '-n', str(path)], check=True)
print('Python and shell syntax passed')
