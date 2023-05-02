#!/bin/bash

declare -A flags
flags=(
    ["--all"]="firefox git node python ssh unsnap zsh"
    ["--initial"]="firefox git node python unsnap zsh slack"
    ["--firefox"]="firefox"
    ["--git"]="git"
    ["--node"]="node"
    ["--python"]="python"
    ["--slack"]="slack"
    ["--ssh"]="ssh"
    ["--unsnap"]="unsnap"
    ["--zsh"]="zsh"
)

info() {
    printf "\033[1;34m👗 INFO: $1\033[0m\n"
}

warning() {
    printf "\033[1;33m👜 WARNING: $1\033[0m\n"
}

error() {
    printf "\033[1;31m👠 ERROR: $1\033[0m\n"
}

success() {
    printf "\033[1;32m🎀 SUCCESS: $1\033[0m\n"
}

if ! command -v apt-get >/dev/null 2>&1; then
    error "This script only supports Debian-based systems."
    exit 1
fi

while [[ "$#" -gt 0 ]]; do
    if [[ ${flags["$1"]+_} ]]; then
        for option in ${flags["$1"]}; do
            declare "$option=true"
        done
        shift
    else
        error "Unknown parameter passed: $1"
        exit 1
    fi
done

function check_sudo() {
    if [[ $(sudo -n uptime 2>&1 | grep "load" | wc -l) -eq 0 ]]; then
        info "Sudo password needed to continue."
        sudo -v
    fi
}

function install_from_deb_link {
    [ -n "$3" ] && command -v "$3" >/dev/null 2>&1 && return
    info "Installing ${1}"
    check_sudo
    export spinner_icon="📦"
    export spinner_msg="Downloading ${1}"
    ./zsh/spinner.zsh curl -fsSL "${2}" -o "${1}"
    export spinner_msg="Installing ${1}"
    ./zsh/spinner.zsh sudo apt-get install -qqy "./${1}"
    export spinner_msg="Cleaning up ${1}"
    ./zsh/spinner.zsh rm "${1}"
}

if [ "$unsnap" = true ]; then
    info "Removing snap packages"
    if command -v snap >/dev/null 2>&1; then
        check_sudo
        if [ -n "$(snap list)" ]; then
            check_sudo
            export spinner_icon="📦"
            export spinner_msg="Removing snap packages"
            ./zsh/spinner.zsh sudo snap remove --purge $(snap list | awk '{print $1}')
        fi
        sudo apt remove --autoremove snap snapd
        sudo mkdir -p /etc/apt/preferences.d/
        echo -e "Package: snapd\nPin: release a=*n\nPin-Priority: -10\n" | sudo tee /etc/apt/preferences.d/nosnap.pref
        sudo apt update
        success "Removed snap packages"
    else
        warning "Snap not installed"
    fi
fi

packages_to_install='git,curl,libbz2-dev,cargo,build-essential'
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
    ./zsh/spinner.zsh sudo apt-get update -qq && sudo apt-get install -qqy $missing_packages
else
    warning "All packages already installed"
fi

if ! command -v brew >/dev/null 2>&1; then
    export spinner_icon="📦"
    export spinner_msg="Installing brew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
    brew install gcc libffi
fi

if [ "$firefox" = true ]; then
    info "Installing Firefox"
    if ! command -v firefox >/dev/null 2>&1; then
        check_sudo
        curl -fsSL "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US" -o "firefox.tar.bz2"
        sudo tar -xjf "firefox.tar.bz2" -C /opt/
        sudo mkdir -p /usr/lib/firefox
        sudo ln -s /opt/firefox/firefox /usr/lib/firefox/firefox
        sudo find ~/.local/share/applications -name "*Firefox*.desktop" -delete
        cp ./firefox/Firefox.desktop ~/.local/share/applications/Firefox.desktop
        mkdir -p ~/.config
        cp ./firefox/mimeapps.list ~/.config/mimeapps.list
        success "Installed Firefox"
    else
        warning "Firefox is already installed"
    fi
fi

if [ "$zsh" = true ]; then
    if ! command -v zsh >/dev/null 2>&1; then
        check_sudo
        export spinner_icon="📦"
        export spinner_msg="Installing zsh"
        ./zsh/spinner.zsh brew install zsh
    else
        warning "zsh is already installed"
    fi
    info "Configuring zsh files"
    cp "$(pwd)/zsh/.zshrc" "${HOME}/.zshrc"
    mkdir -p "${HOME}/.zsh-things"
    files=("git.zsh" "aliases.zsh" "python.zsh" "node.zsh" "spinner.zsh" "rust.zsh")
    for file in "${files[@]}"; do
        cp "$(pwd)/zsh/${file}" "${HOME}/.zsh-things/${file}"
    done
    ln -sf "${HOME}/.zsh-things/spinner.zsh" "${HOME}/.spinner"

    [ "$(basename "$SHELL")" != "zsh" ] && {
    	command -v zsh | sudo tee -a /etc/shells
        chsh -s "$(command -v zsh)"
        info "zsh is now the default shell. Please log in again."
    }

    source "${HOME}/.zshrc"
fi

install_from_deb_link "code_latest_amd64.deb" "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64" "code"
install_from_deb_link "discord.deb" "https://discord.com/api/download?platform=linux&format=deb" "discord"
install_from_deb_link "1password-latest.deb" "https://downloads.1password.com/linux/debian/amd64/stable/1password-latest.deb" "1password"
install_from_deb_link "1password-cli-amd64-latest.deb" "https://downloads.1password.com/linux/debian/amd64/stable/1password-cli-amd64-latest.deb" "op"

if [ "$ssh" = true ]; then
    info "Setting up SSH keys"
    if [ "$(op account list | wc -l)" -eq 0 ]; then
        warning "1Password CLI not signed in. Please sign in and connect the desktop app."
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
        ./zsh/spinner.zsh op read --force --out-file "$3" "op://$2/$1/ssh/$4"
    }

    item_list=$(op item list --favorite)
    item_list=$(echo "$item_list" | tr '[:upper:]' '[:lower:]')

    for vault in "personal" "work"; do
        for service in "github" "gitlab"; do
            pub_key="${HOME}/.ssh/${service}.${vault}.pub"
            priv_key="${HOME}/.ssh/${service}.${vault}"

            if echo "$item_list" | grep "${service}" | grep "${vault}" >/dev/null; then
                info "Fetching $service keys for $vault vault"
                [ ! -f "${pub_key}" ] && sshsetup $service $vault $pub_key public
                [ ! -f "${priv_key}" ] && {
                    sshsetup $service $vault $priv_key private
                    [ -f "${priv_key}" ] && chmod 600 "${priv_key}"
                }
                if [ -f "${priv_key}" ]; then
                    if ! ssh-add -l | grep -q "${priv_key}"; then
                        ssh-add "${priv_key}"
                    fi
                fi
            fi
        done
    done
fi

if [ "$git" = true ]; then
    info "Configuring git files"
    cp "$(pwd)/git/.gitconfig" "${HOME}/.gitconfig"
    cp "$(pwd)/git/.gitignore" "${HOME}/.gitignore"
    cp "$(pwd)/git/.github.gitconfig" "${HOME}/.github.gitconfig"
    cp "$(pwd)/git/.gitlab.gitconfig" "${HOME}/.gitlab.gitconfig"
fi

if [ "$python" = true ]; then
    info "Installing python"
    if ! command -v python >/dev/null 2>&1; then
        export spinner_icon="📦"
        export spinner_msg="Installing python"
        check_sudo
        ./zsh/spinner.zsh brew install python pyenv pipenv
        info "Configuring python files"
        mkdir -p "$HOME/.config/pip"
        [[ ! -f "$HOME/.config/pip/pip.conf" ]] && cp "$(pwd)/python/pip.conf" "$HOME/.config/pip/pip.conf"
    else
        warning "Python is already installed"
    fi
fi

if [ "$node" = true ]; then
    info "Installing node"
    if ! command -v node >/dev/null 2>&1; then
        export spinner_icon="📦"
        export spinner_msg="Installing nodejs"
        check_sudo
        ./zsh/spinner.zsh brew install node
    else
        warning "Node is already installed"
    fi
fi

if ! command -v spotify >/dev/null 2>&1; then
    check_sudo
    export spinner_icon="📥"
    export spinner_msg="Installing spotify"
    curl -sS https://download.spotify.com/debian/pubkey_7A3A762FAFD4A51F.gpg | sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg
    echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list
    ./zsh/spinner.zsh sudo apt-get update && sudo apt-get install -qqy spotify-client
fi

if [ "$slack" = true ]; then
    info "Installing slack"
    if ! command -v slack >/dev/null 2>&1; then
        check_sudo
        export spinner_icon="📥"
        export spinner_msg="Installing slack"
        content=$(curl -s https://slack.com/intl/en-au/downloads/instructions/ubuntu)
        deb_link=$(echo "$content" | grep -oP 'https://downloads\.slack-edge\.com/releases/linux/\K[0-9.]+/prod/x64/slack-desktop-[0-9.]+-amd64\.deb')
        deb_link="https://downloads.slack-edge.com/releases/linux/$deb_link"
        curl -sS "$deb_link" -o slack.deb
        ./zsh/spinner.zsh sudo apt-get install -qqy ./slack.deb
        rm slack.deb
    else
        warning "Slack is already installed"
    fi
fi

success "Done!"
