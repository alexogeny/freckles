"""Utilities for applying curated GNOME desktop preferences."""

from __future__ import annotations

from shutil import which
from subprocess import CompletedProcess, run
from typing import Iterable, Sequence

from .debian import is_ubuntu

BASE_GNOME_SETTINGS: Sequence[tuple[str, str, str]] = (
    ("org.gnome.desktop.interface", "clock-show-date", "true"),
    ("org.gnome.desktop.interface", "clock-show-weekday", "true"),
    ("org.gnome.desktop.interface", "clock-format", "'24h'"),
    ("org.gnome.desktop.interface", "color-scheme", "'prefer-dark'"),
    ("org.gnome.desktop.interface", "enable-hot-corners", "false"),
    (
        "org.gnome.desktop.interface",
        "monospace-font-name",
        "'Cascadia Code 11'",
    ),
    ("org.gnome.desktop.interface", "text-scaling-factor", "1.05"),
    ("org.gnome.desktop.media-handling", "automount", "false"),
    ("org.gnome.desktop.media-handling", "automount-open", "false"),
    ("org.gnome.desktop.peripherals.keyboard", "repeat-interval", "25"),
    ("org.gnome.desktop.peripherals.keyboard", "delay", "250"),
    ("org.gnome.desktop.peripherals.touchpad", "tap-to-click", "true"),
    (
        "org.gnome.desktop.peripherals.touchpad",
        "two-finger-scrolling-enabled",
        "true",
    ),
    ("org.gnome.desktop.session", "idle-delay", "900"),
    ("org.gnome.desktop.sound", "event-sounds", "false"),
    ("org.gnome.desktop.sound", "allow-volume-above-100-percent", "true"),
    ("org.gnome.desktop.wm.preferences", "button-layout", "'appmenu:minimize,maximize,close'"),
    ("org.gnome.desktop.wm.preferences", "focus-new-windows", "'smart'"),
    ("org.gnome.desktop.wm.preferences", "resize-with-right-button", "true"),
    ("org.gnome.mutter", "center-new-windows", "true"),
    ("org.gnome.mutter", "edge-tiling", "true"),
    ("org.gnome.shell", "favorite-apps", "['firefox.desktop', 'code.desktop', 'org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop', 'org.gnome.Calculator.desktop']"),
    ("org.gnome.shell.app-switcher", "current-workspace-only", "true"),
    ("org.gnome.settings-daemon.plugins.color", "night-light-enabled", "true"),
    ("org.gnome.settings-daemon.plugins.color", "night-light-temperature", "3700"),
    ("org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-type", "'nothing'"),
    ("org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-timeout", "1800"),
    ("org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-type", "'suspend'"),
)

DEFAULT_THEME_SETTINGS: Sequence[tuple[str, str, str]] = (
    ("org.gnome.desktop.interface", "cursor-theme", "'Adwaita'"),
    ("org.gnome.desktop.interface", "gtk-theme", "'Adwaita-dark'"),
    ("org.gnome.desktop.interface", "icon-theme", "'Adwaita'"),
)

UBUNTU_THEME_SETTINGS: Sequence[tuple[str, str, str]] = (
    ("org.gnome.desktop.interface", "cursor-theme", "'Yaru'"),
    ("org.gnome.desktop.interface", "gtk-theme", "'Yaru-purple-dark'"),
    ("org.gnome.desktop.interface", "icon-theme", "'Yaru-purple'"),
)

OPTIONAL_SETTINGS: Sequence[tuple[str, str, str]] = (
    ("org.gnome.desktop.interface", "accent-color", "'purple'"),
)

CUSTOM_KEYBINDING_SCHEMA = (
    "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
)
CUSTOM_KEYBINDING_ROOT = (
    "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
)
CUSTOM_KEYBINDINGS: Sequence[dict[str, str]] = (
    {
        "slug": "launch-terminal",
        "name": "Launch Terminal",
        "command": "gnome-terminal",
        "binding": "<Super>Return",
    },
    {
        "slug": "launch-vscode",
        "name": "Launch VS Code",
        "command": "code",
        "binding": "<Super>e",
    },
)


def configure_gnome() -> None:
    """Apply a curated set of GNOME desktop preferences if available."""

    if which("gsettings") is None:
        # GNOME is not installed or ``gsettings`` is unavailable.
        return

    for schema, key, value in _build_settings():
        _apply_setting(schema, key, value)

    for schema, key, value in OPTIONAL_SETTINGS:
        if _is_setting_supported(schema, key):
            _apply_setting(schema, key, value)

    _configure_custom_keybindings(CUSTOM_KEYBINDINGS)


def _build_settings() -> Sequence[tuple[str, str, str]]:
    """Return the GNOME settings tailored to the detected distribution."""

    theme_settings = UBUNTU_THEME_SETTINGS if is_ubuntu() else DEFAULT_THEME_SETTINGS
    return (*BASE_GNOME_SETTINGS, *theme_settings)


def _is_setting_supported(schema: str, key: str) -> bool:
    """Return ``True`` when ``schema`` exposes ``key``."""

    result = run(
        ["gsettings", "describe", schema, key],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    output = (result.stderr or "") + (result.stdout or "")
    return "No such key" not in output


def _configure_custom_keybindings(bindings: Iterable[dict[str, str]]) -> None:
    bindings = list(bindings)
    if not bindings:
        return

    binding_paths = [
        f"{CUSTOM_KEYBINDING_ROOT}/{binding['slug']}/" for binding in bindings
    ]

    list_literal = "[" + ", ".join(f"'{path}'" for path in binding_paths) + "]"
    _apply_setting(
        "org.gnome.settings-daemon.plugins.media-keys",
        "custom-keybindings",
        list_literal,
    )

    for binding, path in zip(bindings, binding_paths, strict=True):
        schema = f"{CUSTOM_KEYBINDING_SCHEMA}:{path}"
        _apply_setting(schema, "name", f"'{binding['name']}'")
        _apply_setting(schema, "command", f"'{binding['command']}'")
        _apply_setting(schema, "binding", f"'{binding['binding']}'")


def _apply_setting(schema: str, key: str, value: str) -> CompletedProcess[str]:
    result = run(
        ["gsettings", "set", schema, key, value],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        if message:
            print(f"Failed to apply {schema} {key}: {message}")
        else:
            print(f"Failed to apply {schema} {key}")
    return result
