from __future__ import annotations

from freckles.application.helpers import step
from freckles.firefox import (
    EXTENSIONS_TO_INSTALL,
    apply_firefox_containers,
    apply_firefox_handlers,
    apply_firefox_policies,
    apply_firefox_user_chrome,
    apply_firefox_user_js,
    extension_already_installed,
    find_firefox_profile,
    get_extension_json,
    install_firefox_extension,
    install_regular_firefox,
    is_firefox_esr_installed,
    purge_esr_profiles,
    purge_firefox_esr,
    setup_mozilla_repo,
)
from utils.ubuntu import ensure_firefox_from_apt
from utils.debian import is_ubuntu


def configure_firefox(reporter) -> None:
    with step(reporter, "Ensure correct Firefox variant"):
        if is_firefox_esr_installed():
            reporter.log("Firefox ESR detected. Purging and installing regular Firefox.")
            purge_firefox_esr()
            with step(reporter, "Configure Mozilla repository"):
                setup_mozilla_repo()
            with step(reporter, "Install regular Firefox"):
                install_regular_firefox()
            with step(reporter, "Remove ESR profiles"):
                purge_esr_profiles()
        elif is_ubuntu():
            ensure_firefox_from_apt()
        else:
            reporter.log("Firefox ESR not detected; no variant changes required.")

    with step(reporter, "Apply Firefox policies"):
        apply_firefox_policies()

    with step(reporter, "Customize Firefox profile"):
        profile = find_firefox_profile()
        if profile is None:
            reporter.log(
                "Skipping Firefox profile customization and extension installation because no profile was found."
            )
            reporter.log("Launch Firefox once to create a profile and rerun this phase if needed.")
            return
        with step(reporter, "Apply user.js preferences"):
            apply_firefox_user_js(profile)
        with step(reporter, "Apply userChrome.css"):
            apply_firefox_user_chrome(profile)
        with step(reporter, "Apply containers.json"):
            apply_firefox_containers(profile)
        extension_data = get_extension_json(profile)
        with step(reporter, "Install Firefox extensions"):
            for extension_id, extension_name in EXTENSIONS_TO_INSTALL.items():
                if extension_already_installed(extension_data, extension_name):
                    reporter.log(f"Extension '{extension_name}' already installed. Skipping.")
                    continue
                install_firefox_extension(extension_id)
        with step(reporter, "Apply handlers.json"):
            apply_firefox_handlers(profile)
