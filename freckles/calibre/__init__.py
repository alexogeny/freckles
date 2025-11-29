"""Calibre library configuration and remote mounting helpers."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from freckles.system.debian import install_with_apt, run
from freckles.core.meta import CONFIG_DIR, HOME

CALIBRE_CONFIG_PATH = CONFIG_DIR / "calibre.json"
CALIBRE_SUPPORT_DIR = CONFIG_DIR / "calibre"
SYSTEMD_USER_DIR = HOME / ".config" / "systemd" / "user"
SYSTEMD_SERVICE_PATH = SYSTEMD_USER_DIR / "calibre-library.service"
MOUNT_SCRIPT_PATH = CALIBRE_SUPPORT_DIR / "mount_remote_library.sh"
MOUNT_PACKAGES = ["sshfs", "rsync"]


def _normalise_directory(path: str) -> str:
    expanded = Path(path).expanduser()
    try:
        relative = expanded.relative_to(HOME)
    except ValueError:
        return expanded.as_posix()
    return f"~/{relative.as_posix()}"


def _prompt(prompt: str, default: Optional[str] = None, allow_empty: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            response = input(f"{prompt}{suffix}: ").strip()
        except EOFError:
            return default or ""
        if not response and default is not None:
            response = default
        if response:
            return response
        if allow_empty:
            return ""
        print("Value is required. Please try again.")


def _prompt_choice(prompt: str, choices: list[str], default: Optional[str] = None) -> str:
    normalised_choices = [choice.lower() for choice in choices]
    default_value = default.lower() if default else None
    options = ", ".join(normalised_choices)
    while True:
        answer = _prompt(f"{prompt} ({options})", default=default_value)
        if answer.lower() in normalised_choices:
            return answer.lower()
        print(f"Please choose one of: {options}.")


@dataclass
class CalibreConfig:
    mode: str
    library_path: str
    remote_url: str = ""
    username: str = ""

    def __post_init__(self) -> None:
        self.mode = self.mode.strip().lower() or "local"
        self.library_path = _normalise_directory(self.library_path.strip())
        self.remote_url = self.remote_url.strip()
        self.username = self.username.strip()

    @property
    def local_path(self) -> Path:
        if self.library_path.startswith("~/"):
            return HOME / self.library_path[2:]
        return Path(self.library_path).expanduser()

    @property
    def remote_target(self) -> str:
        if self.mode != "hosted":
            return ""
        target = self.remote_url
        if self.username and "@" not in target.split(":", 1)[0]:
            target = f"{self.username}@{target}"
        return target

    def as_serialisable(self) -> dict:
        return asdict(self)


def _default_calibre_config() -> CalibreConfig:
    default_path = "~/Documents/Calibre Library"
    return CalibreConfig(mode="local", library_path=default_path)


def load_calibre_config() -> Optional[CalibreConfig]:
    if not CALIBRE_CONFIG_PATH.exists():
        return None
    data = json.loads(CALIBRE_CONFIG_PATH.read_text())
    return CalibreConfig(**data)


def save_calibre_config(config: CalibreConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = config.as_serialisable()
    CALIBRE_CONFIG_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def prompt_for_calibre_config(existing: Optional[CalibreConfig] = None) -> CalibreConfig:
    default_mode = existing.mode if existing else "local"
    mode = _prompt_choice(
        "Is your Calibre library local or hosted remotely?", ["local", "hosted"], default=default_mode
    )

    default_path = existing.library_path if existing else "~/Documents/Calibre Library"
    library_path = _prompt("Local Calibre library path", default=default_path)

    remote_url = existing.remote_url if existing else ""
    username = existing.username if existing else ""
    if mode == "hosted":
        remote_url = _prompt(
            "Remote library location (e.g. example.com:/path/to/library)", default=remote_url or None
        )
        username = _prompt("Username for remote host", default=username or None)
    else:
        remote_url = ""
        username = ""

    return CalibreConfig(mode=mode, library_path=library_path, remote_url=remote_url, username=username)


def ensure_calibre_config(interactive: bool = True) -> CalibreConfig:
    config = load_calibre_config()
    if config:
        if not interactive or not sys.stdin.isatty():
            return config
        if interactive and sys.stdin.isatty():
            if _prompt_choice(
                "Existing Calibre configuration found. Keep it or reconfigure?", ["keep", "reconfigure"], default="keep"
            ) == "reconfigure":
                config = prompt_for_calibre_config(config)
                save_calibre_config(config)
        return config

    if not interactive or not sys.stdin.isatty():
        config = _default_calibre_config()
        save_calibre_config(config)
        return config

    config = prompt_for_calibre_config()
    save_calibre_config(config)
    return config


def _install_mount_dependencies() -> None:
    result = install_with_apt(MOUNT_PACKAGES)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        print(f"Warning: failed to install mount dependencies ({', '.join(MOUNT_PACKAGES)}): {message}")


def _write_mount_script(config: CalibreConfig) -> None:
    CALIBRE_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    local_path = config.local_path
    script_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f"LOCAL_PATH={sh_quote(local_path.as_posix())}",
        f"REMOTE_TARGET={sh_quote(config.remote_target)}",
        "",
        "mkdir -p \"${LOCAL_PATH}\"",
        "if mountpoint -q \"${LOCAL_PATH}\"; then",
        "    exit 0",
        "fi",
        "",
        "if [[ -z \"${REMOTE_TARGET}\" ]]; then",
        "    echo 'Remote target not configured. Skipping mount.'",
        "    exit 0",
        "fi",
        "",
        "sshfs \"${REMOTE_TARGET}\" \"${LOCAL_PATH}\" -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3",
    ]
    MOUNT_SCRIPT_PATH.write_text("\n".join(script_lines) + "\n")
    os.chmod(MOUNT_SCRIPT_PATH, 0o755)


def _write_systemd_service(config: CalibreConfig) -> None:
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    content = f"""[Unit]
Description=Ensure Calibre library is mounted
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart={MOUNT_SCRIPT_PATH.as_posix()}
RemainAfterExit=yes

[Install]
WantedBy=default.target
"""
    SYSTEMD_SERVICE_PATH.write_text(content)
    os.chmod(SYSTEMD_SERVICE_PATH, 0o644)


def _reload_systemd_daemon() -> None:
    run(["systemctl", "--user", "daemon-reload"])


def _enable_mount_service() -> None:
    run(["systemctl", "--user", "enable", "--now", "calibre-library.service"])


def _disable_mount_service() -> None:
    run(["systemctl", "--user", "disable", "--now", "calibre-library.service"])


def configure_calibre(interactive: bool = True) -> CalibreConfig:
    config = ensure_calibre_config(interactive=interactive)
    local_path = config.local_path
    local_path.mkdir(parents=True, exist_ok=True)

    if config.mode == "hosted" and config.remote_target:
        _install_mount_dependencies()
        _write_mount_script(config)
        _write_systemd_service(config)
        _reload_systemd_daemon()
        _enable_mount_service()
        print(
            "Configured Calibre remote library mount. The systemd user service "
            "'calibre-library.service' will attempt to mount the library once the network is ready."
        )
    else:
        if SYSTEMD_SERVICE_PATH.exists():
            _disable_mount_service()
            SYSTEMD_SERVICE_PATH.unlink(missing_ok=True)
        if MOUNT_SCRIPT_PATH.exists():
            MOUNT_SCRIPT_PATH.unlink()
        _reload_systemd_daemon()
    return config


def sh_quote(value: str) -> str:
    """Return a shell-escaped version of ``value`` suitable for scripts."""

    if not value:
        return "''"
    if all(c.isalnum() or c in "@%_-+=:,./" for c in value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"

__all__ = ["configure_calibre", "CalibreConfig", "ensure_calibre_config"]
