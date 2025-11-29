from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CommandInvocation:
    """Represents a single command request."""

    command: str
    cwd: Optional[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass
class CommandRunner:
    """Executes shell commands with support for noop and capture modes."""

    mode: str = "real"
    history: List[CommandInvocation] = field(default_factory=list)

    def run(self, command: str, *, cwd: Optional[str] = None) -> subprocess.CompletedProcess[str]:
        if self.mode == "noop":
            invocation = CommandInvocation(command=command, cwd=cwd, returncode=0, stdout="", stderr="")
            self.history.append(invocation)
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

        result = subprocess.run(command, capture_output=True, text=True, shell=True, cwd=cwd)
        if self.mode == "capture":
            invocation = CommandInvocation(
                command=command,
                cwd=cwd,
                returncode=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
            )
            self.history.append(invocation)
        return result


_runner: Optional[CommandRunner] = None


def configure_runner(mode: str = "real") -> CommandRunner:
    """Configure the global command runner mode."""
    global _runner
    _runner = CommandRunner(mode=mode)
    return _runner


def current_runner() -> CommandRunner:
    global _runner
    if _runner is None:
        _runner = CommandRunner()
    return _runner


def run_command(command: str, *, cwd: Optional[str] = None) -> subprocess.CompletedProcess[str]:
    """Execute ``command`` via the configured runner."""
    return current_runner().run(command, cwd=cwd)
