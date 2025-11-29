from __future__ import annotations

from freckles.application.helpers import step
from freckles.application.identity_service import configure_identity
from utils.bun import install_bun
from utils.vscode import configure_vscode


def configure_developer_tooling(reporter) -> None:
    with step(reporter, "Configure VS Code"):
        configure_vscode()

    with step(reporter, "Configure Git & SSH"):
        configure_identity(reporter)

    with step(reporter, "Install Bun runtime"):
        install_bun()
