#!/bin/bash

declare -A flags
flags=(
    ["--all"]="firefox git node python ssh unsnap zsh"
    ["--pop"]="brew node python ssh zsh slack git vscode bun noisetorch"
    ["--ubuntu"]="firefox git node python unsnap zsh slack"
    ["--firefox"]="firefox"
    ["--git"]="git"
    ["--node"]="node"
    ["--python"]="python"
    ["--slack"]="slack"
    ["--ssh"]="ssh"
    ["--unsnap"]="unsnap"
    ["--zsh"]="zsh"
    ["--brew"]="brew"
    ["--vscode"]="vscode"
    ["--bun"]="bun"
    ["--docker"]="docker"
    ["--noisetorch"]="noisetorch"
)

info() {
    printf "\033[1;34m🐾 INFO: $1\033[0m\n"
}

warning() {
    printf "\033[1;33m🐉 WARNING: $1\033[0m\n"
}

error() {
    printf "\033[1;31m💥 ERROR: $1\033[0m\n"
}

success() {
    printf "\033[1;32m💃🏻 SUCCESS: $1\033[0m\n"
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

spinner() {
    export spinner_icon=${1:-"📦"}
    export spinner_msg=$2
}

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
    spinner "Downloading ${1}"
    ./zsh/spinner.zsh curl -fsSL "${2}" -o "${1}"
    spinner "Installing ${1}"
    ./zsh/spinner.zsh sudo apt-get install -qqy "./${1}"
    spinner "Cleaning up ${1}"
    ./zsh/spinner.zsh rm "${1}"
}

if [ "$unsnap" = true ]; then
    info "Removing snap packages"
    if command -v snap >/dev/null 2>&1; then
        check_sudo
        if [ -n "$(snap list)" ]; then
            check_sudo
            spinner "Removing snap packages"
            ./zsh/spinner.zsh sudo snap remove --purge $(snap list | awk '{print $1}')
        fi
        sudo apt remove --autoremove snap snapd
        sudo mkdir -p /etc/apt/preferences.d/
        echo -e "Package: snapd\nPin: release a=*n\nPin-Priority: -10\n" | sudo tee /etc/apt/preferences.d/nosnap.pref
        sudo apt update
        success "Removed snap packages"
    fi
fi

packages_to_install='git,curl,libbz2-dev,cargo,build-essential,libsqlite3-dev,nginx'
missing_packages=''

IFS=',' read -ra packages <<<"$packages_to_install"
for package in "${packages[@]}"; do
    if ! dpkg -s "$package" >/dev/null 2>&1; then
        missing_packages="${missing_packages} ${package}"
    fi
done

if [ -n "$missing_packages" ]; then
    check_sudo
    spinner "Installing missing packages: ${missing_packages}"
    ./zsh/spinner.zsh sudo apt-get update -qq && sudo apt-get install -qqy $missing_packages
fi

if ! command -v brew >/dev/null 2>&1; then
    spinner "Installing brew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
    brew install gcc libffi
    success "Installed brew"
fi

if [ "$firefox" = "true" ]; then
    if ! command -v firefox >/dev/null 2>&1; then
        info "Installing Firefox"
        check_sudo
        if ! curl -fsSL "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US" -o "firefox.tar.bz2"; then
            error "Failed to download Firefox"
            exit 1
        fi
        if ! sudo tar -xjf "firefox.tar.bz2" -C /opt/; then
            error "Failed to extract Firefox"
            exit 1
        fi
        sudo mkdir -p /usr/lib/firefox
        sudo ln -s /opt/firefox/firefox /usr/lib/firefox/firefox
        sudo find ~/.local/share/applications -name "*Firefox*.desktop" -exec rm -f {} \;
        cp -f ./firefox/Firefox.desktop ~/.local/share/applications/Firefox.desktop
        mkdir -p ~/.config
        cp -f ./firefox/mimeapps.list ~/.config/mimeapps.list
        success "Installed Firefox"
    fi
fi

if [ "$docker" = "true" ]; then
    if ! command -v docker >/dev/null 2>&1; then
        info "Setting up docker"
        check_sudo
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        newgrp docker
        rm -f get-docker.sh
    fi
fi

if [ "$noisetorch" = "true" ]; then
    if ! command -v noisetorch >/dev/null 2>&1; then
        info "Installing NoiseTorch"
        check_sudo
        RELEASES_URL="https://api.github.com/repos/noisetorch/NoiseTorch/releases/latest"
        RELEASE_DATA=$(curl -s $RELEASES_URL)
        ASSET_URL=$(echo $RELEASE_DATA | jq -r '.assets[] | select(.name | test(".tgz$")) | .browser_download_url')
        CHECKSUM=$(echo $RELEASE_DATA | jq -r '.assets[] | select(.name | test("sha512sum")) | .browser_download_url')

        if [ -z "$ASSET_URL" ] || [ -z "$CHECKSUM" ]; then
            error "Failed to find the download URL or checksum for the x64 asset."
            exit 1
        fi
        info "Downloading NoiseTorch latest release..."
        curl -L -o noisetorch-x64.tar.gz $ASSET_URL
        curl -L -o noisetorch-x64.sha512sum $CHECKSUM
        info "Verifying checksum..."
        read -r CHECKSUM_FILE CHECKSUM_FILE_NAME <<<$(cat noisetorch-x64.sha512sum)
        CHECKSUM_CALCULATED=$(sha512sum noisetorch-x64.tar.gz | awk '{print $1}')
        if [ "$CHECKSUM_FILE" != "$CHECKSUM_CALCULATED" ]; then
            error "Checksum verification failed. Expected $CHECKSUM_FILE_NAME to be $CHECKSUM_FILE, but got $CHECKSUM_CALCULATED"
            exit 1
        fi
        info "Unpacking NoiseTorch..."
        tar -C $HOME -h -xzf noisetorch-x64.tar.gz
        info "Updating icon cache..."
        gtk-update-icon-cache
        info "Setting capabilities on NoiseTorch..."
        sudo setcap 'CAP_SYS_RESOURCE=+ep' "$HOME/.local/bin/noisetorch"
        rm -f noisetorch-x64.tar.gz noisetorch-x64.sha512sum
        success "NoiseTorch installed successfully!"
    fi
fi

install_zsh() {
    if ! command -v zsh >/dev/null 2>&1; then
        check_sudo
        spinner "Installing zsh"
        ./zsh/spinner.zsh brew install zsh
    fi
}

configure_zsh_files() {
    info "Configuring zsh files"
    cp "$(pwd)/zsh/.zshrc" "${HOME}/.zshrc"
    mkdir -p "${HOME}/.zsh-things"
    pass=$(op read "op://personal/github/encrypted files")
    if [ ! -f "$(pwd)/salt" ]; then
        op read --force --out-file "$(pwd)/salt" op://personal/github/salt
    fi
    if [ ! -f "$(pwd)/zsh/services.zsh" ]; then
        openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 500000 -in "$(pwd)/zsh/secure/services.zsh.enc" \
            -out "$(pwd)/zsh/services.zsh" -pass "pass:$pass"
    fi
    files=("git.zsh" "aliases.zsh" "python.zsh" "node.zsh" "spinner.zsh" "rust.zsh" "start.zsh" "cds_helper.py" "services.zsh")
    for file in "${files[@]}"; do
        cp "$(pwd)/zsh/${file}" "${HOME}/.zsh-things/${file}"
    done
    ln -sf "${HOME}/.zsh-things/spinner.zsh" "${HOME}/.spinner"
}

set_zsh_as_default() {
    if [[ "$(basename "$SHELL")" != "zsh" ]]; then
        command -v zsh | sudo tee -a /etc/shells
        chsh -s "$(command -v zsh)"
        info "zsh is now the default shell. Please log in again."
    fi
}

source_zshrc() {
    source "${HOME}/.zshrc"
}

install_from_deb_link "code_latest_amd64.deb" "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64" "code"
install_from_deb_link "discord.deb" "https://discord.com/api/download?platform=linux&format=deb" "discord"
install_from_deb_link "1password-latest.deb" "https://downloads.1password.com/linux/debian/amd64/stable/1password-latest.deb" "1password"
install_from_deb_link "1password-cli-amd64-latest.deb" "https://downloads.1password.com/linux/debian/amd64/stable/1password-cli-amd64-latest.deb" "op"

sshsetup() {
    spinner "🔑" "Fetching $1 $4 SSH key for $2 vault"
    "$(dirname "$0")/zsh/spinner.zsh" op read --force --out-file "$3" "op://$2/$1/ssh/$4" || {
        error "Failed to fetch $1 $4 SSH key for $2 vault"
        return 1
    }
}

if [ "$ssh" = true ]; then
    info "Setting up SSH keys"
    if [ "$(op account list | wc -l)" -eq 0 ]; then
        warning "1Password CLI not signed in. Please sign in and connect the desktop app."
        while [ "$(op account list | wc -l)" -eq 0 ]; do
            sleep 10
        done
    fi

    ssh_dir="${HOME}/.ssh"
    mkdir -p "${ssh_dir}" && chmod 700 "${ssh_dir}"

    for file in "config" "known_hosts"; do
        cp "$(pwd)/ssh/$file" "${ssh_dir}/$file" && chmod 600 "${ssh_dir}/$file"
    done

    item_list=$(op item list --favorite)
    item_list=$(echo "$item_list" | tr '[:upper:]' '[:lower:]')

    for vault in "personal" "work"; do
        for service in "github" "gitlab"; do
            pub_key="${ssh_dir}/${service}.${vault}.pub"
            priv_key="${ssh_dir}/${service}.${vault}"

            if echo "$item_list" | grep -q "${service}.*${vault}"; then
                [ ! -f "${pub_key}" ] && sshsetup $service $vault $pub_key public
                [ ! -f "${priv_key}" ] && {
                    sshsetup $service $vault $priv_key private
                    [ -f "${priv_key}" ] && chmod 600 "${priv_key}"
                }
                if [ -f "${priv_key}" ]; then
                    if ! ssh-add -l | grep -q "${priv_key}"; then
                        ssh-add "${priv_key}" || {
                            error "Failed to add $priv_key to SSH agent"
                        }
                    fi
                fi
            fi
        done
    done
fi

if [[ "$zsh" == true ]]; then
    install_zsh
    configure_zsh_files
    set_zsh_as_default
    source_zshrc
fi

if [ "$git" = true ]; then
    info "Configuring git files"

    GIT_FILES=("git/.gitconfig" "git/.gitignore" "git/.github.gitconfig" "git/.gitlab.gitconfig")

    for file in "${GIT_FILES[@]}"; do
        src_file="$(pwd)/$file"
        dest_file="${HOME}/${file##*/}"

        if [ -f "$src_file" ]; then
            cp -f "$src_file" "$dest_file"
            success "Copied $src_file to $dest_file"
        else
            warning "Source file not found: $src_file"
        fi
    done
fi

if [ "$python" = true ]; then
    info "Installing python"
    if ! command -v python >/dev/null 2>&1; then
        spinner "Installing python"
        check_sudo
        ./zsh/spinner.zsh brew install python pyenv pipenv
        info "Configuring python files"
        mkdir -p "$HOME/.config/pip"
        [[ ! -f "$HOME/.config/pip/pip.conf" ]] && cp "$(pwd)/python/pip.conf" "$HOME/.config/pip/pip.conf"
    fi
fi

if [ "$node" = true ]; then
    info "Installing node"
    if ! command -v node >/dev/null 2>&1; then
        spinner "Installing nodejs"
        check_sudo
        ./zsh/spinner.zsh brew install node nvm
        mkdir -p "$HOME/.nvm"
    fi
fi

if [ "$bun" = true ]; then
    info "Installing bun"
    if ! command -v bun >/dev/null 2>&1; then
        spinner "Adding bun tap"
        check_sudo
        ./zsh/spinner.zsh brew tap oven-sh/bun
        export spinner_msg="Installing bun"
        ./zsh/spinner.zsh brew install bun
    fi
fi

if ! command -v spotify >/dev/null 2>&1; then
    check_sudo
    spinner "📥" "Installing spotify"
    curl -sS https://download.spotify.com/debian/pubkey_6224F9941A8AA6D1.gpg | sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg
    echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list
    ./zsh/spinner.zsh sudo apt-get update && sudo apt-get install -qqy spotify-client
fi

if ! command -v aws >/dev/null 2>&1; then
    check_sudo
    spinner "📥" "Installing aws cli"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
fi

if [[ "$slack" == "true" ]]; then
    if ! command -v slack >/dev/null 2>&1; then
        info "Installing slack"
        check_sudo
        spinner "📥" "Installing slack"

        content=$(curl -s https://slack.com/intl/en-au/downloads/instructions/ubuntu) || {
            error "Failed to download Slack information"
            exit 1
        }
        deb_link=$(echo "$content" | grep -oP 'https://downloads\.slack-edge\.com/releases/linux/\K[0-9.]+/prod/x64/slack-desktop-[0-9.]+-amd64\.deb') || {
            error "Failed to extract Slack deb package link"
            exit 1
        }
        deb_link="https://downloads.slack-edge.com/releases/linux/$deb_link"
        slack_tempfile=$(mktemp)
        curl -sS "$deb_link" -o "$slack_tempfile" || {
            error "Failed to download Slack deb package"
            rm -f "$slack_tempfile"
            exit 1
        }

        ./zsh/spinner.zsh sudo dpkg -i "$slack_tempfile" || {
            ./zsh/spinner.zsh sudo apt-get install -qqy -f
            success "Dependencies fixed and Slack installed"
        }

        rm -f "$slack_tempfile"
    fi
fi

configure_nginx() {
    info "Configuring nginx"
    sudo cp "$(pwd)/dev/hosts" "/etc/hosts"
    sudo cp "$(pwd)/dev/nginx.conf" "/etc/nginx/nginx.conf"
    sudo systemctl restart nginx
}

configure_nginx

if [[ "$vscode" == "true" ]]; then
    info "Copying vscode files"
    cp "$(pwd)/vscode/settings.link.json" "${HOME}/.config/Code/User/settings.json"
    cp "$(pwd)/vscode/keybinds.link.json" "${HOME}/.config/Code/User/keybindings.json"
    while read -r extension; do
        [[ -z "$extension" ]] && continue
        code --list-extensions | grep -q "$extension" && continue
        info "Installing vscode extension: $extension"
        code --install-extension "$extension"
    done <"$(pwd)/vscode/extensions.txt"

fi

disable_swap() {
    readarray -t swapfiles < <(awk 'NR > 1 {print $1}' /proc/swaps)

    if [ "${#swapfiles[@]}" -gt 0 ]; then
        check_sudo
        info "Disabling swap"
        for swapfile in "${swapfiles[@]}"; do
            sudo swapoff "$swapfile" || {
                error "Error: swapoff failed for $swapfile" >&2
                exit 1
            }
            sudo rm "$swapfile" || {
                error "Error: failed to remove $swapfile" >&2
                exit 1
            }
        done
        sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab || {
            error "Error: failed to modify /etc/fstab" >&2
            exit 1
        }
    fi
}

disable_swap

fs_watchers() {
    if [ "$(sysctl fs.inotify.max_user_watches | awk '{print $3}')" -lt 524288 ]; then
        check_sudo
        info "Increasing fs.inotify.max_user_watches"
        sudo sysctl -w fs.inotify.max_user_watches=524288
        sudo sysctl -p
    fi
}

fs_watchers

check_and_set_avatar() {
    if [ ! -f "$HOME/.face" ]; then
        info "Setting user avatar"
        curl -s "https://avatars.githubusercontent.com/u/6896115?v=4" -o "$HOME/.face"
    fi
}

update_avatar_if_different() {
    local_avatar_hash=$(md5sum "$HOME/.face" | awk '{print $1}')
    accounts_service_avatar_hash=$(md5sum "/var/lib/AccountsService/icons/$(whoami)" | awk '{print $1}')

    if [ "$local_avatar_hash" != "$accounts_service_avatar_hash" ]; then
        info "Updating user avatar"
        sudo cp "$HOME/.face" "/var/lib/AccountsService/icons/$(whoami)"
        dbus-send --system --print-reply --dest=org.freedesktop.Accounts /org/freedesktop/Accounts/User$(id -u) org.freedesktop.Accounts.User.SetIconFile string:"/var/lib/AccountsService/icons/$(whoami)"
    fi
}

check_and_update_from_remote() {
    if [ ! -f "$HOME/.face" ]; then
        info "No local avatar to update from remote."
        return
    fi

    tmp_file=$(mktemp)
    curl -s "https://avatars.githubusercontent.com/u/6896115?v=4" -o "$tmp_file"
    remote_hash=$(md5sum "$tmp_file" | awk '{print $1}')
    local_hash=$(md5sum "$HOME/.face" | awk '{print $1}')

    if [ "$remote_hash" != "$local_hash" ]; then
        info "Remote avatar has changed. Updating local avatar."
        mv "$tmp_file" "$HOME/.face"
        update_avatar_if_different
    else
        info "Local avatar is up-to-date with remote."
        rm "$tmp_file"
    fi
}

if [ ! -f "$HOME/.face" ]; then
    check_and_set_avatar
else
    check_and_update_from_remote
fi
update_avatar_if_different

rye_rust() {
    # if the rye command does not exist
    if ! command -v rye >/dev/null 2>&1; then
        info "Installing rye"
        check_sudo
        spinner "Installing rye"
        curl -sSf https://rye-up.com/get | bash
    fi
    # if the path $HOME/.rye/tools/ruff does not exist, then run `rye install ruff`
    if [ ! -d "$HOME/.rye/tools/ruff" ]; then
        info "Installing ruff"
        check_sudo
        spinner "Installing ruff"
        "$HOME/.rye/shims/rye" install ruff
        "$HOME/.rye/shims/rye" install ruff-lsp
    fi
}

rye_rust
