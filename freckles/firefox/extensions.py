from __future__ import annotations

from pathlib import Path
from typing import Dict

from utils.debian import run
from utils.web import download_file
from .profiles import find_firefox_profile

EXTENSIONS_TO_INSTALL = {
    "1password-x-password-manager": "1Password – Password Manager",
    "ublock-origin": "uBlock Origin",
    "decentraleyes": "Decentraleyes",
    "vimium-ff": "Vimium",
}


def extension_already_installed(extension_data: Dict, extension_name: str) -> bool:
    for addon in extension_data.get("addons", []):
        if addon.get("defaultLocale", {}).get("name", "") == extension_name:
            return True
    return False


def install_firefox_extension(extension_id: str) -> bool:
    url = (
        "https://addons.mozilla.org/firefox/downloads/latest/"
        f"{extension_id}/addon-{extension_id}-latest.xpi"
    )
    xpi_path: Path | None = None

    try:
        xpi_path = download_file(url, extension_id + ".xpi", overwrite=True)
    except Exception as error:  # pragma: no cover - network failures depend on environment
        print(f"Failed to download extension {extension_id}: {error}")
        return False

    try:
        profile_dir = find_firefox_profile()
        if profile_dir is None:
            print(
                "Unable to install Firefox extension "
                f"{extension_id}: Firefox profile not found."
            )
            return False

        install_command = [
            "firefox",
            "--headless",
            "--no-remote",
            "--profile",
            profile_dir,
            "--install-addon",
            xpi_path.as_posix(),
        ]

        result = run(install_command)
        if result.returncode == 0:
            print(f"Extension {extension_id} installed.")
            return True
        error_output = (result.stderr or result.stdout or "").strip()
        print(f"Error installing extension {extension_id}: {error_output}")
        return False
    except Exception as error:
        print(f"Unexpected error installing extension {extension_id}: {error}")
        return False
    finally:
        if xpi_path is not None:
            xpi_path.unlink(missing_ok=True)

