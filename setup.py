import argparse
import os
import pwd
import sys
from contextlib import contextmanager
from typing import Dict, List, Optional

from freckles.domain.provisioning import Phase
from freckles.infrastructure.command import configure_runner
from freckles.desktop.avatar import manage_avatar
from freckles.system.debian import (
    DebFile,
    DebRepository,
    get_version_codename,
    is_debian_12_bookworm,
    is_debian_like,
    is_ubuntu,
    replace_bookworm_with_trixie,
    run,
    run_apt_update_and_upgrade,
)
from utils.reporter import StepReporter
from freckles.system.web import install_software_list
from freckles.application.packages_service import (
    install_base_packages,
    refresh_package_lists,
    remove_unwanted_packages,
)
from freckles.application.app_setup.developer_tools import configure_developer_tooling
from freckles.system.ubuntu import purge_snapd
from freckles.application.app_setup.firefox_setup import configure_firefox
from freckles.application.app_setup.shell_terminal import configure_shell_terminal
from freckles.application.app_setup.gnome_setup import configure_gnome_desktop
from freckles.application.app_setup.calibre_setup import configure_calibre_library


def _docker_repository_definition() -> DebRepository | None:
    if not is_debian_like():
        return None

    distribution = "ubuntu" if is_ubuntu() else "debian"
    codename_default = "jammy" if distribution == "ubuntu" else "bookworm"
    codename = get_version_codename(codename_default) or codename_default
    repository_url = f"https://download.docker.com/linux/{distribution}"
    sources_entry = "\n".join(
        [
            "Types: deb",
            f"URIs: {repository_url}",
            f"Suites: {codename}",
            "Components: stable",
            "Signed-By: {signed_by}",
            "",
        ]
    )

    return DebRepository(
        name="docker",
        gpg=f"{repository_url}/gpg",
        repository=f"{repository_url} {codename} stable",
        install_name="docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
        check_name="docker",
        sources_entry=sources_entry,
    )


def _ensure_user_in_docker_group(reporter: StepReporter) -> None:
    docker_group = "docker"
    user = os.environ.get("SUDO_USER") or os.environ.get("USER")
    if not user:
        user = pwd.getpwuid(os.getuid()).pw_name

    group_check = run(f"id -Gn {user}")
    if group_check.returncode == 0 and docker_group in (group_check.stdout or "").split():
        reporter.log(f"{user} already belongs to the '{docker_group}' group.")
        return

    reporter.log(f"Adding {user} to the '{docker_group}' group (log out/in to apply).")
    add_result = run(f"sudo usermod -aG {docker_group} {user}")
    if add_result.returncode != 0:
        message = add_result.stderr.strip() or add_result.stdout.strip() or "unknown error"
        reporter.log(f"Unable to add {user} to '{docker_group}': {message}")
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
    DebRepository(
        name="mozilla-vpn",
        gpg="https://packages.mozilla.org/apt/repo-signing-key.gpg",
        repository="https://packages.mozilla.org/apt mozilla main",
        install_name="mozillavpn",
        check_name="mozillavpn",
    ),
]


_docker_repo = _docker_repository_definition()
if _docker_repo:
    software_list.append(_docker_repo)

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
            print(f"  ✔ {entry['name']}")
    if top_level_failures:
        print("Failed phases:")
        for entry in top_level_failures:
            error = entry.get("error", "Unknown error")
            print(f"  ✖ {entry['name']}: {error}")
            nested_failures = failed_descendants(entry["name"])
            for nested in nested_failures:
                nested_error = nested.get("error", "Unknown error")
                print(f"    • {nested['name']}: {nested_error}")
            print("    Fix the issue and rerun `python setup.py` to retry this phase.")
    else:
        print("All phases completed successfully. You're good to go!")


def refresh_apt_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Run apt-get update"):
        refresh_package_lists(software_list, reporter)


def install_base_packages_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Install required base packages"):
        install_base_packages(core_packages)


def ubuntu_cleanup_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Ubuntu-specific cleanup"):
        if not is_ubuntu():
            reporter.log("Skipping because system is not Ubuntu.")
            return
        with managed_step(reporter, "Purge snapd"):
            purge_snapd()


def remove_unwanted_packages_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Remove unwanted packages"):
        remove_unwanted_packages(unwanted_software)


def install_curated_software_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Install curated software"):
        install_software_list(software_list)
        with managed_step(reporter, "Install Bun runtime"):
            install_bun()
        _ensure_user_in_docker_group(reporter)


def configure_developer_tooling_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure developer tooling"):
        configure_developer_tooling(reporter)


def configure_shell_terminal_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure shell and terminal"):
        configure_shell_terminal(reporter)


def configure_gnome_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure GNOME desktop"):
        configure_gnome_desktop(reporter)


def manage_avatar_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Manage avatar"):
        manage_avatar()


def configure_calibre_phase(reporter: StepReporter) -> None:
    with managed_step(reporter, "Configure Calibre"):
        configure_calibre_library(reporter)


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
        configure_firefox(reporter)


def build_phases() -> List[Phase]:
    return [
        Phase("APT refresh", refresh_apt_phase),
        Phase("Base packages", install_base_packages_phase),
        Phase("Ubuntu cleanup", ubuntu_cleanup_phase),
        Phase("Remove stock software", remove_unwanted_packages_phase),
        Phase("Curated software", install_curated_software_phase),
        Phase("Developer tooling", configure_developer_tooling_phase),
        Phase("Shell and terminal", configure_shell_terminal_phase),
        Phase("GNOME setup", configure_gnome_phase),
        Phase("Avatar management", manage_avatar_phase),
        Phase("Calibre setup", configure_calibre_phase),
        Phase("Debian bookworm upgrade", upgrade_bookworm_phase),
        Phase("Firefox configuration", configure_firefox_phase),
    ]


def main() -> None:
    """Entry point for provisioning a workstation."""
    parser = argparse.ArgumentParser(description="Provision a Freckles workstation.")
    parser.add_argument("--noop", action="store_true", help="Log actions without executing shell commands.")
    args, _ = parser.parse_known_args()
    configure_runner("noop" if args.noop else "real")

    if not is_debian_like():
        sys.exit("Freckles currently supports Debian and Ubuntu systems only.")

    phases = build_phases()
    reporter = StepReporter(
        total_top_level=len(phases),
        min_step_duration=0.35,
        enable_animation=True,
        enable_pulse=True,
    )
    try:
        with reporter:
            for phase in phases:
                with managed_step(reporter, phase.name):
                    phase.handler(reporter)
    except Exception:
        if reporter.needs_final_summary:
            emit_summary(reporter.summary())
        raise
    else:
        if reporter.needs_final_summary:
            emit_summary(reporter.summary())


if __name__ == "__main__":
    main()
