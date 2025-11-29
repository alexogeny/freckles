from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

from .templates import (
    CONTAINERS_TEMPLATE,
    HANDLERS_TEMPLATE,
    USER_CHROME_TEMPLATE,
    USER_JS_TEMPLATE,
    read_template,
)


def apply_firefox_user_js(profile_dir: str | Path | None) -> None:
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping user.js provisioning.")
        return

    template_contents = read_template(USER_JS_TEMPLATE, "user.js")
    if template_contents is None:
        return

    profile_path = Path(profile_dir)
    profile_path.mkdir(parents=True, exist_ok=True)
    destination = profile_path / "user.js"
    destination.write_text(template_contents, encoding="utf-8")
    destination.chmod(0o644)
    print(f"Synchronized Firefox user.js template to {destination}.")


def apply_firefox_handlers(profile_dir: str | Path | None) -> None:
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping handlers.json provisioning.")
        return

    template_contents = read_template(HANDLERS_TEMPLATE, "handlers.json")
    if template_contents is None:
        return

    profile_path = Path(profile_dir)
    profile_path.mkdir(parents=True, exist_ok=True)
    destination = profile_path / "handlers.json"
    destination.write_text(template_contents, encoding="utf-8")
    destination.chmod(0o644)
    print(f"Synchronized Firefox handlers template to {destination}.")


def apply_firefox_containers(profile_dir: str | Path | None) -> None:
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping containers.json provisioning.")
        return

    template_contents = read_template(CONTAINERS_TEMPLATE, "containers.json")
    if template_contents is None:
        return

    profile_path = Path(profile_dir)
    profile_path.mkdir(parents=True, exist_ok=True)
    destination = profile_path / "containers.json"
    destination.write_text(template_contents, encoding="utf-8")
    destination.chmod(0o644)
    print(f"Synchronized Firefox containers template to {destination}.")


def apply_firefox_user_chrome(profile_dir: str | Path | None) -> None:
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping userChrome.css provisioning.")
        return

    template_contents = read_template(USER_CHROME_TEMPLATE, "userChrome.css")
    if template_contents is None:
        return

    profile_path = Path(profile_dir)
    chrome_dir = profile_path / "chrome"
    chrome_dir.mkdir(parents=True, exist_ok=True)
    destination = chrome_dir / "userChrome.css"
    destination.write_text(template_contents, encoding="utf-8")
    destination.chmod(0o644)
    print(f"Synchronized Firefox userChrome.css template to {destination}.")


def find_firefox_profile() -> Optional[str]:
    profile_path = Path("~/.mozilla/firefox/").expanduser()

    if not profile_path.exists():
        print(
            "No Firefox profile directory found. Please run Firefox at least once to generate a profile."
        )
        return None

    profile_dirs = [
        d
        for d in profile_path.iterdir()
        if d.is_dir() and (d.name.endswith(".default-esr") or d.name.endswith(".default-release"))
    ]

    if not profile_dirs:
        print(
            "No default Firefox profiles found. Please run Firefox at least once to generate a profile."
        )
        return None

    return str(profile_dirs[0])


def wait_for_firefox_profile() -> Optional[str]:
    profile_dir: Optional[str] = None
    while not profile_dir:
        profile_dir = find_firefox_profile()
        if profile_dir:
            print(f"Profile found: {profile_dir}")
            break
        print("Didn't find firefox profile. Please run and close firefox...")
        time.sleep(5)

    return profile_dir


def get_extension_json(profile_dir: str | Path | None) -> Dict:
    if profile_dir is None:
        print(
            "Firefox profile directory not provided. Skipping extension data lookup."
        )
        return {}

    extensions_file = Path(profile_dir) / "extensions.json"
    if not extensions_file.exists():
        return {}

    try:
        return json.loads(extensions_file.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Unable to parse extensions.json: {exc}")
        return {}

