from __future__ import annotations

import sys

from utils.git import configure_git
from utils.ssh import configure_ssh


def configure_identity(reporter) -> None:
    """Provision git (including GPG) and SSH identities."""

    interactive = sys.stdin.isatty()
    if interactive:
        reporter.log("Configuring git identities interactively. Answer prompts to continue.")
        interactive_ctx = getattr(reporter, "interactive_section", None)
        if callable(interactive_ctx):
            with interactive_ctx():
                configure_git()
        else:
            configure_git()
    else:
        reporter.log("Configuring git identities (non-interactive).")
        configure_git()

    configure_ssh()
