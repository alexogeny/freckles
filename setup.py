from utils import (
    DebFile,
    DebRepository,
    configure_git,
    configure_ssh,
    configure_vscode,
    install_software_list,
)

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