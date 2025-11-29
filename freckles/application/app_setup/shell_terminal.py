from __future__ import annotations

from freckles.application.helpers import step
from freckles.desktop.shell import configure_shell
from freckles.desktop.terminal import configure_terminal


def configure_shell_terminal(reporter) -> None:
    with step(reporter, "Configure shell"):
        configure_shell()
    with step(reporter, "Configure terminal"):
        configure_terminal()
