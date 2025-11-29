"""GNOME Terminal profile customisation for Freckles."""

from __future__ import annotations

import ast
from shutil import which
from subprocess import CompletedProcess, run
from uuid import uuid4

from freckles.core.theme import FRECKLES_TERMINAL_THEME

PROFILE_SETTINGS: dict[str, str] = {
    "audible-bell": "false",
    "background-color": f"'{FRECKLES_TERMINAL_THEME.background}'",
    "background-transparency-percent": "0",
    "bold-color": f"'{FRECKLES_TERMINAL_THEME.bold}'",
    "bold-color-same-as-fg": "false",
    "cursor-background-color": f"'{FRECKLES_TERMINAL_THEME.cursor_background}'",
    "cursor-colors-set": "true",
    "cursor-foreground-color": f"'{FRECKLES_TERMINAL_THEME.cursor_foreground}'",
    "cursor-shape": "'block'",
    "default-size-columns": "120",
    "default-size-rows": "34",
    "font": f"'{FRECKLES_TERMINAL_THEME.font}'",
    "foreground-color": f"'{FRECKLES_TERMINAL_THEME.foreground}'",
    "highlight-background-color": f"'{FRECKLES_TERMINAL_THEME.highlight_background}'",
    "highlight-colors-set": "true",
    "highlight-foreground-color": f"'{FRECKLES_TERMINAL_THEME.highlight_foreground}'",
    "login-shell": "true",
    "palette": "["
    + ", ".join(f"'{colour}'" for colour in FRECKLES_TERMINAL_THEME.palette)
    + "]",
    "scrollbar-policy": "'never'",
    "use-custom-default-size": "true",
    "use-system-font": "false",
    "use-theme-colors": "false",
    "visible-name": f"'{FRECKLES_TERMINAL_THEME.name}'",
}


def configure_terminal() -> None:
    """Synchronise the Freckles GNOME Terminal profile if gsettings exists."""

    if which("gsettings") is None:
        return
    profile_id = _ensure_profile_id()
    if profile_id is None:
        return

    schema = _profile_schema(profile_id)
    for key, value in PROFILE_SETTINGS.items():
        _apply_setting(schema, key, value)
    _set_default_profile(profile_id)


def _ensure_profile_id() -> str | None:
    """Return the Freckles profile id, creating it if needed."""

    for profile in _list_profile_ids():
        if _profile_name(profile) == FRECKLES_TERMINAL_THEME.name:
            return profile

    default_profile = _get_default_profile_id()
    if default_profile:
        _ensure_profile_in_list(default_profile)
        return default_profile

    return _create_profile()


def _get_default_profile_id() -> str | None:
    profile_id = _read_gsetting("org.gnome.Terminal.ProfilesList", "default")
    if profile_id:
        profile_id = profile_id.strip("'")
        return profile_id or None

    profiles = _read_gsetting("org.gnome.Terminal.ProfilesList", "list")
    if not profiles:
        return None

    candidates = [
        profile.strip()
        for profile in profiles.strip("[]").replace("'", "").split(",")
        if profile.strip()
    ]
    return candidates[0] if candidates else None


def _read_gsetting(schema: str, key: str) -> str:
    result = run(
        ["gsettings", "get", schema, key],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def _apply_setting(schema: str, key: str, value: str) -> CompletedProcess[str]:
    return run(
        ["gsettings", "set", schema, key, value],
        capture_output=True,
        text=True,
        check=False,
    )


def _profile_schema(profile_id: str) -> str:
    return (
        "org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:"
        f"{profile_id}/"
    )


def _profile_name(profile_id: str) -> str:
    """Return the visible profile name for ``profile_id``."""

    name = _read_gsetting(_profile_schema(profile_id), "visible-name")
    return _strip_quotes(name)


def _list_profile_ids() -> list[str]:
    """Return all configured GNOME Terminal profile IDs."""

    literal = _read_gsetting("org.gnome.Terminal.ProfilesList", "list")
    if not literal:
        return []
    try:
        parsed = ast.literal_eval(literal)
    except (ValueError, SyntaxError):
        return []
    if not isinstance(parsed, (list, tuple)):
        return []
    ids = []
    for entry in parsed:
        if not isinstance(entry, str):
            continue
        cleaned = _strip_quotes(entry)
        if cleaned:
            ids.append(cleaned)
    return ids


def _ensure_profile_in_list(profile_id: str) -> None:
    ids = _list_profile_ids()
    if profile_id in ids:
        return
    ids.append(profile_id)
    literal = "[" + ", ".join(f"'{profile}'" for profile in ids) + "]"
    _apply_setting("org.gnome.Terminal.ProfilesList", "list", literal)


def _create_profile() -> str:
    profile_id = str(uuid4())
    _ensure_profile_in_list(profile_id)
    return profile_id


def _set_default_profile(profile_id: str) -> None:
    _apply_setting("org.gnome.Terminal.ProfilesList", "default", f"'{profile_id}'")


def _strip_quotes(value: str) -> str:
    return value.strip().strip("'\"") if value else ""


__all__ = ["configure_terminal"]
