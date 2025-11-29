from __future__ import annotations

from typing import Iterable, Set

from utils.debian import (
    DebFile,
    DebRepository,
    ensure_repositories_configured,
    install_with_apt,
    purge_unwanted_packages,
    refresh_repository_keys,
    run,
)


def refresh_package_lists(software_list: list[DebFile | DebRepository], reporter) -> None:
    apt_update_result = run("sudo apt-get update -qq")
    if apt_update_result.returncode != 0:
        combined_output = (apt_update_result.stderr or "") + (apt_update_result.stdout or "")
        if "NO_PUBKEY" in combined_output:
            missing_key_ids: Set[str] = {
                match.group(1).upper()
                for match in __import__("re").finditer(r"NO_PUBKEY\\s+([0-9A-F]+)", combined_output)
            }

            def refresh_keys() -> None:
                reporter.log(
                    f"Refreshing repository keys for: {', '.join(sorted(missing_key_ids)) or 'unknown keys'}"
                )
                refreshed = refresh_repository_keys(software_list, missing_key_ids)
                if not refreshed:
                    ensure_repositories_configured(software_list)

            refresh_keys()
            apt_update_result = run("sudo apt-get update -qq")

        if apt_update_result.returncode != 0:
            message = (apt_update_result.stderr or "").strip() or (apt_update_result.stdout or "").strip()
            raise RuntimeError(f"Failed to refresh apt package lists: {message}")


def install_base_packages(packages: Iterable[str]) -> None:
    essential_install = install_with_apt(list(packages))
    if essential_install.returncode != 0:
        message = essential_install.stderr.strip() or essential_install.stdout.strip()
        raise RuntimeError(f"Failed to install required base packages: {message}")


def remove_unwanted_packages(packages: Iterable[str]) -> None:
    purge_unwanted_packages(list(packages))

