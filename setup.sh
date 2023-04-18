#!/bin/bash

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This script only supports Debian-based systems."
    exit 1
fi

cp "$(pwd)/git/.gitconfig" "${HOME}/.gitconfig"
cp "$(pwd)/git/.gitignore" "${HOME}/.gitignore"
cp "$(pwd)/git/.github.gitconfig" "${HOME}/.github.gitconfig"
cp "$(pwd)/git/.gitlab.gitconfig" "${HOME}/.gitlab.gitconfig"

mkdir -p "${HOME}/.ssh"
cp "$(pwd)/ssh/config" "${HOME}/.ssh/config"

if ! command -v zsh >/dev/null 2>&1; then
    echo "zsh not found, installing..."
    ~/.spinner sudo apt-get update && sudo apt-get install -y zsh
fi

cp "$(pwd)/zsh/.zshrc" "${HOME}/.zshrc"
mkdir -p "${HOME}/.zsh-things"
files=("git.zsh" "aliases.zsh" "python.zsh")

for file in "${files[@]}"; do
    cp "$(pwd)/zsh/${file}" "${HOME}/.zsh-things/${file}"
done
cp "$(pwd)/zsh/.spinner.sh" "${HOME}/.spinner"

if [ "$(basename "$SHELL")" != "zsh" ]; then
    chsh -s "$(command -v zsh)"
    echo "zsh is now the default shell. Please restart your terminal."
fi

source "${HOME}/.zshrc"

if ! command -v curl >/dev/null 2>&1; then
    echo "curl not found, installing..."
    sudo apt-get update && sudo apt-get install -y curl
fi
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

mkdir -p "${HOME}/.config/Code/User"
cp "$(pwd)/vscode/settings.json" "${HOME}/.config/Code/User/settings.json"
cp "$(pwd)/vscode/keybinds.json" "${HOME}/.config/Code/User/keybindings.json"

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
