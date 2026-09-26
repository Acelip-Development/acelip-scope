"""Bounded subprocess execution. No shell, privilege escalation, or repairs."""

from dataclasses import dataclass
import logging
import os
import selectors
import shutil
import signal
import subprocess
import threading
import time

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Result:
    argv: tuple[str, ...]
    stdout: str = ""
    stderr: str = ""
    code: int | None = None
    problem: str = ""

    @property
    def ok(self) -> bool:
        return self.code == 0 and not self.problem

    @property
    def reason(self) -> str:
        return self.problem or self.stderr.strip() or self.stdout.strip() or f"Exit code {self.code}"


class Runner:
    def __init__(self, cancel: threading.Event | None = None, max_bytes: int = 262144):
        self.cancel = cancel or threading.Event()
        self.max_bytes = max_bytes

    def run(self, *argv: str, timeout: float = 7) -> Result:
        args = tuple(argv)
        if self.cancel.is_set():
            return Result(args, problem="Scan cancelled")
        if not args or not shutil.which(args[0]):
            return Result(args, problem=f"Command not installed: {args[0] if args else '(empty)'}")
        if args[0].rsplit('/', 1)[-1] in {"sudo", "pkexec", "su"}:
            return Result(args, problem="Privilege escalation is disabled")
        env = {**os.environ, "LC_ALL": "C", "LANG": "C", "NO_COLOR": "1",
               "SYSTEMD_PAGER": "cat", "SYSTEMD_COLORS": "0", "GIT_OPTIONAL_LOCKS": "0"}
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        problem = ""
        try:
            proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, env=env, start_new_session=True)
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
                    selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
                    deadline = time.monotonic() + timeout
                    while selector.get_map() or proc.poll() is None:
                        if self.cancel.is_set():
                            problem = "Scan cancelled"
                            break
                        if time.monotonic() >= deadline:
                            problem = f"Timed out after {timeout:g} seconds"
                            break
                        for key, _ in selector.select(timeout=min(.1, max(0, deadline - time.monotonic()))):
                            chunk = os.read(key.fileobj.fileno(), 16384)
                            if not chunk:
                                selector.unregister(key.fileobj)
                                continue
                            remaining = self.max_bytes - sum(map(len, buffers.values()))
                            buffers[key.data].extend(chunk[:remaining])
                            if len(chunk) > remaining:
                                problem = f"Output truncated at {self.max_bytes} bytes"
                                break
                        if problem:
                            break
            finally:
                if problem or proc.poll() is None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                try:
                    # Even a device query stuck in kernel I/O must not hold the UI worker forever.
                    proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    problem = (problem + '; ' if problem else '') + 'Process termination still pending'
                proc.stdout.close()
                proc.stderr.close()
            code = proc.returncode
        except OSError as exc:
            LOG.warning("Cannot execute %s: %s", args[0], exc)
            return Result(args, problem=str(exc))
        if problem or code:
            LOG.warning("Check command %s: %s", args[0], problem or f"exit {code}")
        return Result(args, buffers['stdout'].decode(errors='replace'),
                      buffers['stderr'].decode(errors='replace'), code, problem)
