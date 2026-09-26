"""Command result DTO; no execution or operating-system dependencies."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    argv: tuple[str, ...]
    stdout: str = ''
    stderr: str = ''
    code: int | None = None
    problem: str = ''

    @property
    def ok(self):
        return self.code == 0 and not self.problem

    @property
    def reason(self):
        return self.problem or self.stderr.strip() or self.stdout.strip() or f'Exit code {self.code}'
