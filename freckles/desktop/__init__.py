"""Desktop and UI configuration helpers."""

from .gnome import configure_gnome
from .terminal import configure_terminal
from .shell import configure_shell
from .vscode import configure_vscode
from .avatar import manage_avatar

__all__ = [
    "configure_gnome",
    "configure_terminal",
    "configure_shell",
    "configure_vscode",
    "manage_avatar",
]
