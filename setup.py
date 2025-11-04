import re
import sys
from contextlib import contextmanager
from typing import Dict, List, Optional

from utils.avatar import manage_avatar
from utils.calibre import configure_calibre
from utils.debian import (
    DebFile,
    DebRepository,
    install_with_apt,
    is_debian_12_bookworm,
    is_debian_like,
    is_ubuntu,
    purge_unwanted_packages,
    replace_bookworm_with_trixie,
    run,
    run_apt_update_and_upgrade,
)
from utils.firefox import (
    EXTENSIONS_TO_INSTALL,
    apply_firefox_policies,
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
from utils.git import configure_git
from utils.gnome import configure_gnome
from utils.reporter import StepReporter
from utils.shell import configure_shell
from utils.terminal import configure_terminal
from utils.ssh import configure_ssh
from utils.vscode import configure_vscode
from utils.web import (
    ensure_repositories_configured,
    install_software_list,
    refresh_repository_keys,
)
from utils.ubuntu import ensure_firefox_from_apt, purge_snapd


software_list = [
    DebFile(
        name="slack",
        search_url="https://slack.com/downloads/instructions/linux?ddl=1&build=deb",
        pattern=r"https://downloads.slack-edge.com/desktop-releases/linux/x64/[0-9\.]+/slack-desktop-[0-9\.]+-amd64.deb",
        check_name="slack",
        package_name="slack-desktop",
    ),
    DebFile(
        name="code",
        direct_link="https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64",
        check_name="code",
        package_name="code",
    ),
    DebFile(
        name="1password",
        direct_link="https://downloads.1password.com/linux/debian/amd64/stable/1password-latest.deb",
        check_name="1password",
        package_name="1password",
    ),
    DebFile(
        name="op",
        direct_link="https://downloads.1password.com/linux/debian/amd64/stable/1password-cli-amd64-latest.deb",
        check_name="op",
        package_name="1password-cli",
    ),
    DebRepository(
        name="spotify",
        gpg="https://download.spotify.com/debian/pubkey_C85668DF69375001.gpg",
        gpg_template="https://download.spotify.com/debian/pubkey_{key_id}.gpg",
        repository="https://repository.spotify.com stable non-free",
        install_name="spotify-client",
        check_name="spotify",
    ),
]

unwanted_software = [
    "gnome-games",
    "gnome-music",
    "shotwell",
    "rhythmbox",
    "gnome-contacts",
    "libreoffice-*",
    "transmission-*",
    "cups",
    "cups-*",
]

core_packages = [
    "ca-certificates",
    "curl",
    "fonts-cascadia-code",
    "git",
    "calibre",
    "gnupg",
    "lsb-release",
    "make",
    "zsh",
]


@contextmanager
def managed_step(reporter: StepReporter, name: str):
    reporter.start_step(name)
    try:
        yield
    except Exception as exc:  # pragma: no cover - propagation for summary
        reporter.fail_step(name, exc)
        raise
    else:
        reporter.finish_step(name)


def emit_summary(summary: Dict[str, List[Dict[str, Optional[str]]]]) -> None:
    children_by_parent: Dict[Optional[str], List[Dict[str, Optional[str]]]] = {}
    for bucket in ("succeeded", "failed"):
        for entry in summary[bucket]:
            parent = entry.get("parent")
            children_by_parent.setdefault(parent, []).append(entry)

    def failed_descendants(parent_name: str) -> List[Dict[str, Optional[str]]]:
        collected: List[Dict[str, Optional[str]]] = []
        for child in children_by_parent.get(parent_name, []):
            if child.get("status") == "failed":
                collected.append(child)
            collected.extend(failed_descendants(child["name"]))
        return collected

    top_level_success = [entry for entry in summary["succeeded"] if entry.get("depth") == 0]
    top_level_failures = [entry for entry in summary["failed"] if entry.get("depth") == 0]

    print("\n=== Setup Summary ===")
    if top_level_success:
        print("Successful phases:")
        for entry in top_level_success:
            print(f"  - {entry['name']}")
    if top_level_failures:
        print("Failed phases:")
        for entry in top_level_failures:
            error = entry.get("error", "Unknown error")
            print(f"  - {entry['name']}: {error}")
            nested_failures = failed_descendants(entry["name"])
            for nested in nested_failures:
                nested_error = nested.get("error", "Unknown error")
                print(f"    * {nested['name']}: {nested_error}")
            print("    Fix the issue and rerun `python setup.py` to retry this phase.")
    else:
        print("All phases completed successfully. You're good to go!")


def refresh_apt_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Run apt-get update"):
        apt_update_result = run("sudo apt-get update -yqq")
        if apt_update_result.returncode != 0:
            combined_output = (apt_update_result.stderr or "") + (apt_update_result.stdout or "")
            if "NO_PUBKEY" in combined_output:
                missing_key_ids = {
                    match.group(1).upper()
                    for match in re.finditer(r"NO_PUBKEY\\s+([0-9A-F]+)", combined_output)
                }

                def refresh_keys() -> None:
                    reporter.log(
                        f"Refreshing repository keys for: {', '.join(sorted(missing_key_ids)) or 'unknown keys'}"
                    )
                    refreshed = refresh_repository_keys(software_list, missing_key_ids)
                    if not refreshed:
                        ensure_repositories_configured(software_list)

                with managed_step(reporter, "Refresh repository keys"):
                    refresh_keys()

                apt_update_result = run("sudo apt-get update -yqq")

            if apt_update_result.returncode != 0:
                message = (apt_update_result.stderr or "").strip() or (apt_update_result.stdout or "").strip()
                raise RuntimeError(f"Failed to refresh apt package lists: {message}")


def install_base_packages_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Install required base packages"):
        essential_install = install_with_apt(core_packages)
        if essential_install.returncode != 0:
            message = essential_install.stderr.strip() or essential_install.stdout.strip()
            raise RuntimeError(f"Failed to install required base packages: {message}")


def ubuntu_cleanup_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Ubuntu-specific cleanup"):
        if not is_ubuntu():
            reporter.log("Skipping because system is not Ubuntu.")
            return
        with managed_step(reporter, "Purge snapd"):
            purge_snapd()


def remove_unwanted_packages_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Remove unwanted packages"):
        purge_unwanted_packages(unwanted_software)


def install_curated_software_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Install curated software"):
        install_software_list(software_list)


def configure_developer_tooling_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure developer tooling"):
        with managed_step(reporter, "Configure VS Code"):
            configure_vscode()
        with managed_step(reporter, "Configure Git"):
            configure_git()
        with managed_step(reporter, "Configure SSH"):
            configure_ssh()


def configure_shell_terminal_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure shell and terminal"):
        with managed_step(reporter, "Configure shell"):
            configure_shell()
        with managed_step(reporter, "Configure terminal"):
            configure_terminal()


def configure_gnome_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure GNOME desktop"):
        configure_gnome()


def manage_avatar_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Manage avatar"):
        manage_avatar()


def configure_calibre_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure Calibre"):
        configure_calibre()


def upgrade_bookworm_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Handle Debian bookworm upgrade"):
        if is_debian_12_bookworm() is not True:
            reporter.log("Skipping because system is not Debian 12 (bookworm).")
            return
        with managed_step(reporter, "Switch repositories to trixie"):
            replace_bookworm_with_trixie()
        with managed_step(reporter, "Upgrade system packages"):
            run_apt_update_and_upgrade()
        with managed_step(reporter, "Re-purge unwanted packages"):
            purge_unwanted_packages(unwanted_software)


def configure_firefox_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure Firefox"):
        with managed_step(reporter, "Ensure correct Firefox variant"):
            if is_firefox_esr_installed():
                reporter.log("Firefox ESR detected. Purging and installing regular Firefox.")
                with managed_step(reporter, "Purge Firefox ESR"):
                    purge_firefox_esr()
                with managed_step(reporter, "Configure Mozilla repository"):
                    setup_mozilla_repo()
                with managed_step(reporter, "Install regular Firefox"):
                    install_regular_firefox()
                with managed_step(reporter, "Remove ESR profiles"):
                    purge_esr_profiles()
            elif is_ubuntu():
                with managed_step(reporter, "Ensure Firefox from APT"):
                    ensure_firefox_from_apt()
            else:
                reporter.log("Firefox ESR not detected; no variant changes required.")

        with managed_step(reporter, "Apply Firefox policies"):
            apply_firefox_policies()

        with managed_step(reporter, "Customize Firefox profile"):
            profile = find_firefox_profile()
            if profile is None:
                reporter.log(
                    "Skipping Firefox profile customization and extension installation because no profile was found."
                )
                reporter.log("Launch Firefox once to create a profile and rerun this phase if needed.")
                return
            with managed_step(reporter, "Apply user.js preferences"):
                apply_firefox_user_js(profile)
            extension_data = get_extension_json(profile)
            with managed_step(reporter, "Install Firefox extensions"):
                for extension_id, extension_name in EXTENSIONS_TO_INSTALL.items():
                    if extension_already_installed(extension_data, extension_name):
                        reporter.log(f"Extension '{extension_name}' already installed. Skipping.")
                        continue
                    with managed_step(reporter, f"Install extension: {extension_name}"):
                        install_firefox_extension(extension_id)


def main() -> None:
    if not is_debian_like():
        sys.exit("Freckles currently supports Debian and Ubuntu systems only.")

    phases = [
        ("APT refresh", refresh_apt_phase),
        ("Base packages", install_base_packages_phase),
        ("Ubuntu cleanup", ubuntu_cleanup_phase),
        ("Remove stock software", remove_unwanted_packages_phase),
        ("Curated software", install_curated_software_phase),
        ("Developer tooling", configure_developer_tooling_phase),
        ("Shell and terminal", configure_shell_terminal_phase),
        ("GNOME setup", configure_gnome_phase),
        ("Avatar management", manage_avatar_phase),
        ("Calibre setup", configure_calibre_phase),
        ("Debian bookworm upgrade", upgrade_bookworm_phase),
        ("Firefox configuration", configure_firefox_phase),
    ]

    reporter = StepReporter()
    try:
        with reporter:
            for label, phase in phases:
                with managed_step(reporter, label):
                    phase(reporter)
    except Exception:
        emit_summary(reporter.summary())
        raise
    else:
        emit_summary(reporter.summary())


if __name__ == "__main__":
    main()
