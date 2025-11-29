"""System/package management helpers."""

from .debian import (
    DebFile,
    DebRepository,
    check_if_installed,
    get_os_release,
    get_os_release_value,
    get_version_codename,
    install_with_apt,
    is_debian,
    is_debian_12_bookworm,
    is_debian_like,
    is_ubuntu,
    purge_unwanted_packages,
    replace_bookworm_with_trixie,
    run,
    run_apt_update_and_upgrade,
    is_package_installed,
)
from .ubuntu import ensure_firefox_from_apt, purge_snapd
from .web import ensure_repositories_configured, install_software_list, refresh_repository_keys

__all__ = [
    "DebFile",
    "DebRepository",
    "check_if_installed",
    "get_os_release",
    "get_os_release_value",
    "get_version_codename",
    "install_with_apt",
    "is_debian",
    "is_debian_12_bookworm",
    "is_debian_like",
    "is_ubuntu",
    "purge_unwanted_packages",
    "replace_bookworm_with_trixie",
    "run",
    "run_apt_update_and_upgrade",
    "is_package_installed",
    "ensure_firefox_from_apt",
    "purge_snapd",
    "ensure_repositories_configured",
    "install_software_list",
    "refresh_repository_keys",
]
