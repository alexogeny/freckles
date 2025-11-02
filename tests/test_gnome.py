import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import gnome  # noqa: E402


class FakeProcess:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_configure_gnome_requires_gsettings(monkeypatch):
    called = []

    def fake_apply(*args, **kwargs):
        called.append((args, kwargs))
        return FakeProcess()

    monkeypatch.setattr(gnome, "which", lambda _: None)
    monkeypatch.setattr(gnome, "_apply_setting", fake_apply)

    gnome.configure_gnome()

    assert called == []


def test_configure_gnome_applies_curated_settings(monkeypatch):
    commands = []

    def fake_apply(schema: str, key: str, value: str):
        commands.append((schema, key, value))
        return FakeProcess()

    monkeypatch.setattr(gnome, "which", lambda _: "/usr/bin/gsettings")
    monkeypatch.setattr(gnome, "_apply_setting", fake_apply)

    gnome.configure_gnome()

    assert ("org.gnome.desktop.interface", "clock-show-date", "true") in commands

    favorite_apps = (
        "org.gnome.shell",
        "favorite-apps",
        "['firefox.desktop', 'code.desktop', 'org.gnome.Nautilus.desktop', "
        "'org.gnome.Terminal.desktop', 'org.gnome.Calculator.desktop']",
    )
    assert favorite_apps in commands

    terminal_binding_path = f"{gnome.CUSTOM_KEYBINDING_ROOT}/launch-terminal/"
    terminal_binding = (
        f"{gnome.CUSTOM_KEYBINDING_SCHEMA}:{terminal_binding_path}",
        "command",
        "'gnome-terminal'",
    )
    assert terminal_binding in commands

    custom_list_entry = (
        "org.gnome.settings-daemon.plugins.media-keys",
        "custom-keybindings",
        "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/launch-terminal/', "
        "'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/launch-vscode/']",
    )
    assert custom_list_entry in commands
