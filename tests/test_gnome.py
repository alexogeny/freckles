import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import gnome  # noqa: E402
from utils.theme import (  # noqa: E402
    FRECKLES_INTERFACE_THEME,
    FRECKLES_TERMINAL_THEME,
)


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
    monkeypatch.setattr(gnome, "_is_setting_supported", lambda *_: False)
    monkeypatch.setattr(gnome, "_configure_terminal_theme", lambda: called.append("terminal"))

    gnome.configure_gnome()

    assert called == []


def test_configure_gnome_applies_curated_settings(monkeypatch):
    commands = []
    terminal_calls = []
    gtk_calls = []

    def fake_apply(schema: str, key: str, value: str):
        commands.append((schema, key, value))
        return FakeProcess()

    monkeypatch.setattr(gnome, "which", lambda _: "/usr/bin/gsettings")
    monkeypatch.setattr(gnome, "_apply_setting", fake_apply)
    monkeypatch.setattr(gnome, "_is_setting_supported", lambda *_: False)
    monkeypatch.setattr(gnome, "_preferred_cursor_theme", lambda: "Adwaita")
    monkeypatch.setattr(gnome, "_preferred_gtk_theme", lambda: "Adwaita-dark")
    monkeypatch.setattr(gnome, "_preferred_icon_theme", lambda: "Papirus-Dark")
    monkeypatch.setattr(gnome, "_configure_terminal_theme", lambda: terminal_calls.append(True))
    monkeypatch.setattr(gnome, "_apply_gtk_customizations", lambda: gtk_calls.append(True))

    gnome.configure_gnome()

    assert ("org.gnome.desktop.interface", "clock-show-date", "true") in commands
    assert (
        "org.gnome.desktop.interface",
        "gtk-theme",
        "'Adwaita-dark'",
    ) in commands
    assert (
        "org.gnome.desktop.interface",
        "icon-theme",
        "'Papirus-Dark'",
    ) in commands

    assert (
        "org.gnome.desktop.interface",
        "font-name",
        f"'{FRECKLES_INTERFACE_THEME.interface_font}'",
    ) in commands
    assert (
        "org.gnome.desktop.interface",
        "document-font-name",
        f"'{FRECKLES_INTERFACE_THEME.document_font}'",
    ) in commands
    assert (
        "org.gnome.desktop.interface",
        "monospace-font-name",
        f"'{FRECKLES_INTERFACE_THEME.monospace_font}'",
    ) in commands
    assert (
        "org.gnome.desktop.wm.preferences",
        "titlebar-font",
        f"'{FRECKLES_INTERFACE_THEME.titlebar_font}'",
    ) in commands

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
    assert terminal_calls == [True]
    assert gtk_calls == [True]


def test_configure_gnome_uses_curated_theme_on_ubuntu(monkeypatch):
    commands = []
    monkeypatch.setattr(gnome, "_configure_terminal_theme", lambda: None)
    monkeypatch.setattr(gnome, "_apply_gtk_customizations", lambda: None)

    def fake_apply(schema: str, key: str, value: str):
        commands.append((schema, key, value))
        return FakeProcess()

    monkeypatch.setattr(gnome, "which", lambda _: "/usr/bin/gsettings")
    monkeypatch.setattr(gnome, "_apply_setting", fake_apply)
    monkeypatch.setattr(gnome, "_is_setting_supported", lambda *_: False)
    monkeypatch.setattr(gnome, "_preferred_cursor_theme", lambda: "Adwaita")
    monkeypatch.setattr(gnome, "_preferred_gtk_theme", lambda: "Adwaita-dark")
    monkeypatch.setattr(gnome, "_preferred_icon_theme", lambda: "Papirus-Dark")

    gnome.configure_gnome()

    ubuntu_theme = (
        "org.gnome.desktop.interface",
        "gtk-theme",
        "'Adwaita-dark'",
    )
    assert ubuntu_theme in commands


def test_configure_gnome_applies_optional_settings(monkeypatch):
    commands = []
    monkeypatch.setattr(gnome, "_configure_terminal_theme", lambda: None)
    monkeypatch.setattr(gnome, "_apply_gtk_customizations", lambda: None)

    def fake_apply(schema: str, key: str, value: str):
        commands.append((schema, key, value))
        return FakeProcess()

    monkeypatch.setattr(gnome, "which", lambda _: "/usr/bin/gsettings")
    monkeypatch.setattr(gnome, "_apply_setting", fake_apply)
    monkeypatch.setattr(gnome, "_is_setting_supported", lambda *_: True)
    monkeypatch.setattr(gnome, "_preferred_cursor_theme", lambda: "Adwaita")
    monkeypatch.setattr(gnome, "_preferred_gtk_theme", lambda: "Adwaita-dark")
    monkeypatch.setattr(gnome, "_preferred_icon_theme", lambda: "Papirus-Dark")

    gnome.configure_gnome()

    accent = (
        "org.gnome.desktop.interface",
        "accent-color",
        f"'{FRECKLES_INTERFACE_THEME.accent}'",
    )
    assert accent in commands


def test_preferred_gtk_theme_prefers_installed_candidate(tmp_path, monkeypatch):
    theme_dir = tmp_path / "adw-gtk3-dark"
    theme_dir.mkdir()
    monkeypatch.setattr(gnome, "THEME_SEARCH_PATHS", (tmp_path,))

    assert gnome._preferred_gtk_theme() == "adw-gtk3-dark"


def test_preferred_gtk_theme_falls_back_to_default(monkeypatch):
    monkeypatch.setattr(gnome, "THEME_SEARCH_PATHS", tuple())

    assert gnome._preferred_gtk_theme() == "Adwaita-dark"


def test_preferred_icon_theme_prefers_installed_candidate(tmp_path, monkeypatch):
    icon_dir = tmp_path / "Papirus-Dark"
    icon_dir.mkdir()
    monkeypatch.setattr(gnome, "ICON_SEARCH_PATHS", (tmp_path,))

    assert gnome._preferred_icon_theme() == "Papirus-Dark"


def test_preferred_icon_theme_falls_back_to_default(monkeypatch):
    monkeypatch.setattr(gnome, "ICON_SEARCH_PATHS", tuple())

    assert gnome._preferred_icon_theme() == "Adwaita"


def test_preferred_cursor_theme_prefers_installed_candidate(tmp_path, monkeypatch):
    cursor_dir = tmp_path / "Bibata-Modern-Classic"
    cursor_dir.mkdir()
    monkeypatch.setattr(gnome, "ICON_SEARCH_PATHS", (tmp_path,))

    assert gnome._preferred_cursor_theme() == "Bibata-Modern-Classic"


def test_preferred_cursor_theme_falls_back_to_default(monkeypatch):
    monkeypatch.setattr(gnome, "ICON_SEARCH_PATHS", tuple())

    assert gnome._preferred_cursor_theme() == "Adwaita"


def test_apply_gtk_customizations_writes_templates(tmp_path, monkeypatch):
    gtk3_template = tmp_path / "gtk3.css"
    gtk4_template = tmp_path / "gtk4.css"
    gtk3_template.write_text("gtk3")
    gtk4_template.write_text("gtk4")

    monkeypatch.setattr(gnome, "GTK3_TEMPLATE", gtk3_template)
    monkeypatch.setattr(gnome, "GTK4_TEMPLATE", gtk4_template)

    config_root = tmp_path / "config-home"

    monkeypatch.setattr(gnome.Path, "home", lambda: config_root)

    gnome._apply_gtk_customizations()

    gtk3_dest = config_root / ".config" / "gtk-3.0" / "gtk.css"
    gtk4_dest = config_root / ".config" / "gtk-4.0" / "gtk.css"

    assert gtk3_dest.exists()
    assert gtk4_dest.exists()
    assert gtk3_dest.read_text() == "gtk3"
    assert gtk4_dest.read_text() == "gtk4"


def test_default_terminal_profile_id_parses_output(monkeypatch):
    monkeypatch.setattr(
        gnome,
        "run",
        lambda *_, **__: FakeProcess(stdout="'1234-uuid'")
    )

    assert gnome._default_terminal_profile_id() == "1234-uuid"


def test_default_terminal_profile_id_handles_failure(monkeypatch):
    monkeypatch.setattr(
        gnome,
        "run",
        lambda *_, **__: FakeProcess(returncode=1)
    )

    assert gnome._default_terminal_profile_id() is None


def test_configure_terminal_theme_applies_settings(monkeypatch):
    commands = []

    monkeypatch.setattr(gnome, "_default_terminal_profile_id", lambda: "profile-id")
    monkeypatch.setattr(gnome, "_apply_setting", lambda *args: (commands.append(args), FakeProcess())[1])

    gnome._configure_terminal_theme()

    profile_schema = f"{gnome.TERMINAL_PROFILE_SCHEMA}:{gnome.TERMINAL_PROFILES_ROOT}profile-id/"
    assert (
        profile_schema,
        "background-color",
        f"'{FRECKLES_TERMINAL_THEME.background}'",
    ) in commands

    palette_commands = [cmd for cmd in commands if cmd[1] == "palette"]
    assert len(palette_commands) == 1
    assert palette_commands[0][2] == gnome._serialize_palette(
        FRECKLES_TERMINAL_THEME.palette
    )


def test_configure_terminal_theme_no_profile(monkeypatch):
    monkeypatch.setattr(gnome, "_default_terminal_profile_id", lambda: None)
    monkeypatch.setattr(gnome, "_apply_setting", lambda *_, **__: (_ for _ in ()).throw(AssertionError))

    gnome._configure_terminal_theme()
