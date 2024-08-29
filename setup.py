from utils.debian import (
    DebFile,
    DebRepository,
    is_debian_12_bookworm,
    replace_bookworm_with_trixie,
    run_apt_update_and_upgrade,
)
from utils.firefox import (
    EXTENSIONS_TO_INSTALL,
    extension_already_installed,
    find_firefox_profile,
    get_extension_json,
    install_firefox_extension,
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

install_software_list(software_list)
configure_vscode()
configure_ssh()
configure_git()
configure_shell()
if is_debian_12_bookworm() is True:
    replace_bookworm_with_trixie()
    run_apt_update_and_upgrade()
else:
    print("Not upgrading to trixie")
# if get_firefox_version().endswith("esr"):
#     print("Upgrading from firefox esr")
#     upgrade_firefox()
# else:
#     print("Already on firefox main channel")

profile = find_firefox_profile()
extension_data = get_extension_json(profile)
for extension_id, extension_name in EXTENSIONS_TO_INSTALL.items():
    if extension_already_installed(extension_data, extension_name):
        continue
    install_firefox_extension(extension_id)
