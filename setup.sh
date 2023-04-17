#!/bin/bash

# Create symlinks for git
cp "$(pwd)/git/.gitconfig" "${HOME}/.gitconfig"
cp "$(pwd)/git/.gitignore" "${HOME}/.gitignore"
cp "$(pwd)/git/.github.gitconfig" "${HOME}/.github.gitconfig"
cp "$(pwd)/git/.gitlab.gitconfig" "${HOME}/.gitlab.gitconfig"

# Create symlinks for ssh
mkdir -p "${HOME}/.ssh"
cp "$(pwd)/ssh/config" "${HOME}/.ssh/config"

# Check if VSCode is installed and install it if not
if ! command -v code >/dev/null 2>&1; then
    echo "VSCode not found, installing..."
    if command -v apt-get >/dev/null 2>&1; then
        # Ubuntu, Debian
        curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
        sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
        rm packages.microsoft.gpg

        echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/vscode stable main" | sudo tee /etc/apt/sources.list.d/vscode.list

        sudo apt-get update
        sudo apt-get install -y code
    elif command -v pacman >/dev/null 2>&1; then
        # Arch, Manjaro
        sudo pacman -Syu
        git clone https://aur.archlinux.org/visual-studio-code-bin.git
        cd visual-studio-code-bin
        makepkg -si
        cd ..
        rm -rf visual-studio-code-bin
    else
        echo "Package manager not supported, please install VSCode manually."
        exit 1
    fi
fi


# Create symlinks for vscode
mkdir -p "${HOME}/.config/Code/User"
cp "$(pwd)/vscode/settings.json" "${HOME}/.config/Code/User/settings.json"
cp "$(pwd)/vscode/keybinds.json" "${HOME}/.config/Code/User/keybindings.json"

# Install and configure zsh
if ! command -v zsh >/dev/null 2>&1; then
    echo "zsh not found, installing..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y zsh
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S zsh
    else
        echo "Package manager not supported, please install zsh manually."
        exit 1
    fi
fi

# Create symlink for .zshrc
cp "$(pwd)/zsh/.zshrc" "${HOME}/.zshrc"
mkdir -p "${HOME}/.zsh-things"
cp "$(pwd)/zsh/.git.zsh" "${HOME}/.zsh-things/.git.zsh"
cp "$(pwd)/zsh/.spinner.sh" "${HOME}/.spinner"

# Set zsh as the default shell for the current user
if [ "$(basename "$SHELL")" != "zsh" ]; then
    chsh -s "$(command -v zsh)"
    echo "zsh is now the default shell. Please restart your terminal."
fi
