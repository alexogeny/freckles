from __future__ import annotations

from freckles.application.helpers import step
from freckles.desktop.gnome import configure_gnome


def configure_gnome_desktop(reporter) -> None:
    with step(reporter, "Configure GNOME desktop"):
        configure_gnome()
