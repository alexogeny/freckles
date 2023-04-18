#!/bin/bash

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This script only supports Debian-based systems."
    exit 1
fi

function check_sudo() {
    if [[ $(sudo -n uptime 2>&1|grep "load"|wc -l) -eq 0 ]]; then
        sudo -v
    fi
}

if ! command -v zsh >/dev/null 2>&1; then
    echo "zsh not found, installing..."
    check_sudo
    ~/.spinner sudo apt-get update && sudo apt-get install -y zsh
fi

cp "$(pwd)/zsh/.zshrc" "${HOME}/.zshrc"
mkdir -p "${HOME}/.zsh-things"
files=("git.zsh" "aliases.zsh" "python.zsh" "node.zsh" "spinner.zsh")
for file in "${files[@]}"; do
    cp "$(pwd)/zsh/${file}" "${HOME}/.zsh-things/${file}"
done
ln -sf "${HOME}/.zsh-things/spinner.zsh" "${HOME}/.spinner"

if [ "$(basename "$SHELL")" != "zsh" ]; then
    chsh -s "$(command -v zsh)"
    echo "zsh is now the default shell. Please restart your terminal."
fi

source "${HOME}/.zshrc"

if ! command -v curl >/dev/null 2>&1; then
    echo "curl not found, installing..."
    sudo apt-get update && sudo apt-get install -y curl
fi

if ! command -v 1password >/dev/null 2>&1; then
    echo "1Password not found, installing..."
    check_sudo
    export spinner_icon="📥"
    export spinner_msg="Downloading 1Password"
    ~/.spinner curl -fsSL https://downloads.1password.com/linux/debian/amd64/stable/1password-latest.deb -o 1password-latest.deb
    export spinner_icon="📦"
    export spinner_msg="Installing 1Password"
    ~/.spinner sudo apt-get install -qqy ./1password-latest.deb
    export spinner_icon="🧹"
    export spinner_msg="Cleaning up"
    ~/.spinner rm 1password-latest.deb
fi

if ! command -v op >/dev/null 2>&1; then
    echo "1Password CLI not found, installing..."
    check_sudo
    export spinner_icon="📥"
    export spinner_msg="Downloading 1Password CLI"
    ~/.spinner curl -fsSL https://downloads.1password.com/linux/debian/amd64/stable/1password-cli-amd64-latest.deb -o 1password-cli-amd64-latest.deb
    export spinner_icon="📦"
    export spinner_msg="Installing 1Password CLI"
    ~/.spinner sudo apt-get install -qqy ./1password-cli-amd64-latest.deb
    export spinner_icon="🧹"
    export spinner_msg="Cleaning up"
    ~/.spinner rm 1password-cli-amd64-latest.deb
fi

# check 'op account list', and if it's empty, prompt the user to sign in and connect the desktop app
if [ "$(op account list | wc -l)" -eq 0 ]; then
    echo "1Password CLI not signed in. Please sign in and connect the desktop app."
    1password
    while [ "$(op account list | wc -l)" -eq 0 ]; do
        sleep 10
    done
fi

mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
cp "$(pwd)/ssh/config" "${HOME}/.ssh/config"
chmod 600 "${HOME}/.ssh/config"
for vault in "personal" "work"; do
    for service in "github" "gitlab"; do
        pub_key="${HOME}/.ssh/${service}.${vault}.pub"
        priv_key="${HOME}/.ssh/${service}.${vault}"
        if [ ! -f "${pub_key}" ]; then
            export spinner_icon="🔑"
            export spinner_msg="Fetching ${service} public SSH key for ${vault} vault"
            ~/.spinner op read --force --out-file "${pub_key}" "op://${vault}/${service}/ssh/public"
        fi
        if [ ! -f "${priv_key}" ]; then
            export spinner_icon="🔑"
            export spinner_msg="Fetching ${service} private SSH key for ${vault} vault"
            ~/.spinner op read --force --out-file "${priv_key}" "op://${vault}/${service}/ssh/private"
            if [ -f "${priv_key}" ]; then
                chmod 600 "${priv_key}"
            fi
        fi
    done
done

cp "$(pwd)/git/.gitconfig" "${HOME}/.gitconfig"
cp "$(pwd)/git/.gitignore" "${HOME}/.gitignore"
cp "$(pwd)/git/.github.gitconfig" "${HOME}/.github.gitconfig"
cp "$(pwd)/git/.gitlab.gitconfig" "${HOME}/.gitlab.gitconfig"


if ! command -v pip3 >/dev/null 2>&1; then
    echo "pip3 not found, installing..."
    ~/.spinner sudo apt-get update && sudo apt-get install -y python3-pip
fi

if [ ! -d "$HOME/.pyenv" ]; then
    echo "pyenv not found, installing..."
    curl https://pyenv.run | bash
    echo "pyenv installed, please restart your terminal."
    exit 1
fi

if ! command -v pipenv >/dev/null 2>&1; then
    echo "pipenv not found, installing..."
    ~/.spinner pip3 install --user --break-system-packages pipenv
fi

# Check if VSCode is installed and install it if not
if ! command -v code >/dev/null 2>&1; then
    echo "VSCode not found, installing..."
    # Ubuntu, Debian
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor >packages.microsoft.gpg
    sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
    rm packages.microsoft.gpg

    echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/vscode stable main" | sudo tee /etc/apt/sources.list.d/vscode.list

    sudo apt-get update
    sudo apt-get install -y code
fi

# mkdir -p "${HOME}/.config/Code/User"
# cp "$(pwd)/vscode/settings.json" "${HOME}/.config/Code/User/settings.json"
# cp "$(pwd)/vscode/keybinds.json" "${HOME}/.config/Code/User/keybindings.json"

if ! command -v node >/dev/null 2>&1; then
    echo "node.js not found, installing..."
    curl -sL https://deb.nodesource.com/setup_current.x | sudo -E bash -
    ~/.spinner sudo apt-get install -qy nodejs npm
fi

if ! command -v nvm >/dev/null 2>&1; then
    echo "nvm not found, installing..."
    nvm_latest_version=$(curl -s https://api.github.com/repos/nvm-sh/nvm/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/${nvm_latest_version}/install.sh | bash
fi
