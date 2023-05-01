#!/bin/bash

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This script only supports Debian-based systems."
    exit 1
fi

function check_sudo() {
    if [[ $(sudo -n uptime 2>&1 | grep "load" | wc -l) -eq 0 ]]; then
        sudo -v
    fi
}

function install_from_deb_link {
    [ -n "$3" ] && command -v "$3" >/dev/null 2>&1 && return
    check_sudo
    export spinner_icon="📦"
    export spinner_msg="Downloading and installing ${1}"
    ./zsh/spinner.zsh curl -fsSL "${2}" -o "${1}"
    ./zsh/spinner.zsh sudo apt-get install -qqy "./${1}"
    ./zsh/spinner.zsh rm "${1}"
}

if command -v snap >/dev/null 2>&1; then
    check_sudo
    if [ -n "$(snap list)" ]; then
        check_sudo
        export spinner_icon="📦"
        export spinner_msg="Removing snap packages"
        ./zsh/spinner.zsh sudo snap remove --purge $(snap list | awk '{print $1}')
    fi
    sudo apt remove --autoremove snapd
    sudo mkdir -p /etc/apt/preferences.d/
    echo -e "Package: snapd\nPin: release a=*n\nPin-Priority: -10\n" | sudo tee /etc/apt/preferences.d/nosnap.pref
    sudo apt update
fi

packages_to_install='git,zsh,curl,python3-pip,libbz2-dev,python3-virtualenv,cargo,build-essential'
missing_packages=''
for package in $(echo "$packages_to_install" | tr ',' '\n'); do
    if ! dpkg -s "$package" >/dev/null 2>&1; then
        missing_packages="${missing_packages} ${package}"
    fi
done
if [ -n "$missing_packages" ]; then
    check_sudo
    export spinner_icon="📦"
    export spinner_msg="Installing missing packages: ${missing_packages}"
    ./zsh/spinner.zsh sudo apt-get update -qq && sudo apt-get install -qqy "$missing_packages"
fi

if ! command -v firefox >/dev/null 2>&1; then
    check_sudo
    curl -fsSL "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US" -o "firefox.tar.bz2"
    sudo tar -xjf "firefox.tar.bz2" -C /opt/
    sudo ln -s /opt/firefox/firefox /usr/lib/firefox/firefox
fi

cp "$(pwd)/zsh/.zshrc" "${HOME}/.zshrc"
mkdir -p "${HOME}/.zsh-things"
files=("git.zsh" "aliases.zsh" "python.zsh" "node.zsh" "spinner.zsh" "rust.zsh")
for file in "${files[@]}"; do
    cp "$(pwd)/zsh/${file}" "${HOME}/.zsh-things/${file}"
done
ln -sf "${HOME}/.zsh-things/spinner.zsh" "${HOME}/.spinner"

[ "$(basename "$SHELL")" != "zsh" ] && {
    chsh -s "$(command -v zsh)"
    echo "zsh is now the default shell. Please restart your terminal."
}

source "${HOME}/.zshrc"

install_from_deb_link "code_latest_amd64.deb" "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64" "code"
install_from_deb_link "discord.deb" "https://discord.com/api/download?platform=linux&format=deb" "discord"
install_from_deb_link "1password-latest.deb" "https://downloads.1password.com/linux/debian/amd64/stable/1password-latest.deb" "1password"
install_from_deb_link "1password-cli-amd64-latest.deb" "https://downloads.1password.com/linux/debian/amd64/stable/1password-cli-amd64-latest.deb" "op"

if [ "$(op account list | wc -l)" -eq 0 ]; then
    echo "1Password CLI not signed in. Please sign in and connect the desktop app."
    while [ "$(op account list | wc -l)" -eq 0 ]; do
        sleep 10
    done
fi

mkdir -p "${HOME}/.ssh" && chmod 700 "${HOME}/.ssh"

for file in "config" "known_hosts"; do
    cp "$(pwd)/ssh/$file" "${HOME}/.ssh/$file" && chmod 600 "${HOME}/.ssh/$file"
done

sshsetup() {
    export spinner_icon="🔑"
    export spinner_msg="Fetching $1 public SSH key for $2 vault"
    ./zsh/spinner.zsh op read --force --out-file "$3" "op://$2/$1/ssh/public"
}

for vault in "personal" "work"; do
    for service in "github" "gitlab"; do
        pub_key="${HOME}/.ssh/${service}.${vault}.pub"
        priv_key="${HOME}/.ssh/${service}.${vault}"

        [ ! -f "${pub_key}" ] && sshsetup $service $vault $pub_key
        [ ! -f "${priv_key}" ] && {
            sshsetup $service $vault $priv_key
            [ -f "${priv_key}" ] && chmod 600 "${priv_key}"
        }
    done
done

cp "$(pwd)/git/.gitconfig" "${HOME}/.gitconfig"
cp "$(pwd)/git/.gitignore" "${HOME}/.gitignore"
cp "$(pwd)/git/.github.gitconfig" "${HOME}/.github.gitconfig"
cp "$(pwd)/git/.gitlab.gitconfig" "${HOME}/.gitlab.gitconfig"

mkdir -p "$HOME/.config/pip"
[[ ! -f "$HOME/.config/pip/pip.conf" ]] && cp "$(pwd)/python/pip.conf" "$HOME/.config/pip/pip.conf"

[[ ! -d "$HOME/.pyenv" ]] && {
    export spinner_icon="🐍"
    export spinner_msg="Installing pyenv"
    curl https://pyenv.run | bash
}

command -v pipenv >/dev/null 2>&1 || {
    export spinner_icon="🐍"
    export spinner_msg="Installing pipenv"
    ./zsh/spinner.zsh pip3 install --user --break-system-packages pipenv
}

if ! command -v node >/dev/null 2>&1; then
    export spinner_icon="📦"
    export spinner_msg="Installing nodejs"
    check_sudo
    ./zsh/spinner.zsh curl -sL https://deb.nodesource.com/setup_current.x | sudo -E bash - &&
        sudo apt-get install -qy nodejs npm
fi

if ! command -v nvm >/dev/null 2>&1; then
    export spinner_icon="📦"
    export spinner_msg="Installing nvm"
    nvm_latest_version=$(curl -s https://api.github.com/repos/nvm-sh/nvm/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    ./zsh/spinner.zsh curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/${nvm_latest_version}/install.sh | bash
fi

if ! command -v spotify >/dev/null 2>&1; then
    check_sudo
    export spinner_icon="📥"
    export spinner_msg="Installing spotify"
    curl -sS https://download.spotify.com/debian/pubkey_7A3A762FAFD4A51F.gpg | sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg
    echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list
    ./zsh/spinner.zsh sudo apt-get update && sudo apt-get install -qqy spotify-client
fi
