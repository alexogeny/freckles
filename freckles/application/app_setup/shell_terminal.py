from __future__ import annotations

from freckles.application.helpers import step
from utils.shell import configure_shell
from utils.terminal import configure_terminal


def configure_shell_terminal(reporter) -> None:
    with step(reporter, "Configure shell"):
        configure_shell()
    with step(reporter, "Configure terminal"):
        configure_terminal()

