"""GNOME Terminal profile customisation for Freckles."""

from __future__ import annotations

from shutil import which
from subprocess import CompletedProcess, run


TERMINAL_PALETTE: tuple[str, ...] = (
    "rgb(23, 23, 27)",
    "rgb(230, 130, 130)",
    "rgb(104, 201, 129)",
    "rgb(246, 202, 113)",
    "rgb(125, 178, 255)",
    "rgb(172, 129, 255)",
    "rgb(97, 212, 214)",
    "rgb(234, 232, 252)",
    "rgb(70, 74, 85)",
    "rgb(255, 151, 151)",
    "rgb(125, 222, 149)",
    "rgb(255, 213, 128)",
    "rgb(146, 189, 255)",
    "rgb(194, 160, 255)",
    "rgb(128, 226, 228)",
    "rgb(247, 247, 252)",
)

PROFILE_SETTINGS: dict[str, str] = {
    "audible-bell": "false",
    "background-color": "'rgb(13, 16, 24)'",
    "background-transparency-percent": "0",
    "bold-color": "'rgb(157, 179, 255)'",
    "bold-color-same-as-fg": "false",
    "cursor-background-color": "'rgb(255, 210, 111)'",
    "cursor-colors-set": "true",
    "cursor-foreground-color": "'rgb(13, 16, 24)'",
    "cursor-shape": "'block'",
    "default-size-columns": "120",
    "default-size-rows": "34",
    "font": "'Cascadia Code 12'",
    "foreground-color": "'rgb(234, 232, 252)'",
    "highlight-background-color": "'rgb(62, 70, 90)'",
    "highlight-colors-set": "true",
    "highlight-foreground-color": "'rgb(245, 245, 250)'",
    "login-shell": "true",
    "palette": "[" + ", ".join(f"'{colour}'" for colour in TERMINAL_PALETTE) + "]",
    "scrollbar-policy": "'never'",
    "use-custom-default-size": "true",
    "use-system-font": "false",
    "use-theme-colors": "false",
    "visible-name": "'Freckles Midnight'",
}


def configure_terminal() -> None:
    """Synchronise the Freckles GNOME Terminal profile if gsettings exists."""

    if which("gsettings") is None:
        return

    default_profile = _get_default_profile_id()
    if default_profile is None:
        return

    profile_schema = (
        "org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:"
        f"{default_profile}/"
    )

    for key, value in PROFILE_SETTINGS.items():
        _apply_setting(profile_schema, key, value)


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


__all__ = ["configure_terminal"]
