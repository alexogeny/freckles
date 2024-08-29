from pathlib import Path

from .meta import REPOSITORY_LATEST
from .web import download_file


def configure_vscode():
    vscode = Path.home() / ".config" / "Code" / "User"
    if not vscode.exists():
        vscode.mkdir(parents=True, exist_ok=True)
    settings, keybindings = vscode / "settings.json", vscode / "keybindings.json"
    if not settings.exists():
        download_file(
            REPOSITORY_LATEST + "vscode/settings.link.json",
            "settings.json",
        )
        Path("settings.json").rename(settings)
    if not keybindings.exists():
        download_file(
            REPOSITORY_LATEST + "vscode/keybinds.link.json",
            "keybinds.json",
        )
        Path("keybinds.json").rename(keybindings)
