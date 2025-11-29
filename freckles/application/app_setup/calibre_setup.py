from __future__ import annotations

from freckles.application.helpers import step
from freckles.calibre import configure_calibre


def configure_calibre_library(reporter) -> None:
    with step(reporter, "Configure Calibre"):
        with reporter.interactive_section():
            configure_calibre()
