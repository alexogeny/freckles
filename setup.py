from utils.avatar import manage_avatar
from utils.debian import (
    DebFile,
    DebRepository,
    is_debian_12_bookworm,
    purge_unwanted_packages,
    replace_bookworm_with_trixie,
    run_apt_update_and_upgrade,
)
from utils.firefox import (
    EXTENSIONS_TO_INSTALL,
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
from utils.shell import configure_shell
from utils.ssh import configure_ssh
from utils.vscode import configure_vscode
from utils.web import install_software_list

software_list = [
    DebFile(
        name="slack",
        search_url="https://slack.com/downloads/instructions/linux?ddl=1&build=deb",
        pattern=r"https://downloads.slack-edge.com/desktop-releases/linux/x64/[0-9\.]+/slack-desktop-[0-9\.]+-amd64.deb",
    ),
    DebFile(
        name="code",
        direct_link="https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64",
    ),
    DebFile(
        name="1password",
        direct_link="https://downloads.1password.com/linux/debian/amd64/stable/1password-latest.deb",
    ),
    DebFile(
        name="op",
        direct_link="https://downloads.1password.com/linux/debian/amd64/stable/1password-cli-amd64-latest.deb",
    ),
    DebRepository(
        name="spotify",
        gpg="https://download.spotify.com/debian/pubkey_6224F9941A8AA6D1.gpg",
        repository="http://repository.spotify.com stable non-free",
        install_name="spotify-client",
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

purge_unwanted_packages(unwanted_software)
install_software_list(software_list)
configure_vscode()
configure_ssh()
configure_git()
configure_shell()
manage_avatar()
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

profile = find_firefox_profile()
extension_data = get_extension_json(profile)
for extension_id, extension_name in EXTENSIONS_TO_INSTALL.items():
    if extension_already_installed(extension_data, extension_name):
        continue
    install_firefox_extension(extension_id)
