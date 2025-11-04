import re
import sys

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


if not is_debian_like():
    sys.exit("Freckles currently supports Debian and Ubuntu systems only.")

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

apt_update_result = run("sudo apt-get update -yqq")
if apt_update_result.returncode != 0:
    combined_output = (apt_update_result.stderr or "") + (apt_update_result.stdout or "")
    if "NO_PUBKEY" in combined_output:
        missing_key_ids = {
            match.group(1).upper()
            for match in re.finditer(r"NO_PUBKEY\\s+([0-9A-F]+)", combined_output)
        }
        refreshed = refresh_repository_keys(software_list, missing_key_ids)
        if not refreshed:
            ensure_repositories_configured(software_list)
        apt_update_result = run("sudo apt-get update -yqq")

if apt_update_result.returncode != 0:
    message = (apt_update_result.stderr or "").strip() or (apt_update_result.stdout or "").strip()
    sys.exit(f"Failed to refresh apt package lists: {message}")

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

essential_install = install_with_apt(core_packages)
if essential_install.returncode != 0:
    message = essential_install.stderr.strip() or essential_install.stdout.strip()
    sys.exit(f"Failed to install required base packages: {message}")

if is_ubuntu():
    purge_snapd()

purge_unwanted_packages(unwanted_software)
install_software_list(software_list)
configure_vscode()
configure_git()
configure_ssh()
configure_shell()
configure_terminal()
configure_gnome()
manage_avatar()
configure_calibre()
if is_debian_12_bookworm() is True:
    replace_bookworm_with_trixie()
    run_apt_update_and_upgrade()
    purge_unwanted_packages(unwanted_software)
if is_firefox_esr_installed():
    print("Firefox ESR detected. Purging and installing regular Firefox.")
    purge_firefox_esr()
    setup_mozilla_repo()
    install_regular_firefox()
    purge_esr_profiles()
elif is_ubuntu():
    ensure_firefox_from_apt()

apply_firefox_policies()

profile = find_firefox_profile()
if profile is None:
    print(
        "Skipping Firefox profile customization and extension installation because "
        "no profile was found. Launch Firefox once to create a profile and rerun "
        "this step if needed."
    )
else:
    apply_firefox_user_js(profile)
    extension_data = get_extension_json(profile)
    for extension_id, extension_name in EXTENSIONS_TO_INSTALL.items():
        if extension_already_installed(extension_data, extension_name):
            continue
        install_firefox_extension(extension_id)
