"""Firefox domain and infrastructure helpers."""

from .policies import apply_firefox_policies
from .profiles import (
    apply_firefox_containers,
    apply_firefox_handlers,
    apply_firefox_user_chrome,
    apply_firefox_user_js,
    find_firefox_profile,
    get_extension_json,
    wait_for_firefox_profile,
)
from .extensions import (
    EXTENSIONS_TO_INSTALL,
    extension_already_installed,
    install_firefox_extension,
)
from .install import (
    get_firefox_version,
    install_regular_firefox,
    is_firefox_esr_installed,
    purge_esr_profiles,
    purge_firefox_esr,
    setup_mozilla_repo,
)

__all__ = [
    "apply_firefox_policies",
    "apply_firefox_containers",
    "apply_firefox_handlers",
    "apply_firefox_user_chrome",
    "apply_firefox_user_js",
    "find_firefox_profile",
    "wait_for_firefox_profile",
    "get_extension_json",
    "EXTENSIONS_TO_INSTALL",
    "extension_already_installed",
    "install_firefox_extension",
    "get_firefox_version",
    "install_regular_firefox",
    "is_firefox_esr_installed",
    "purge_esr_profiles",
    "purge_firefox_esr",
    "setup_mozilla_repo",
]
