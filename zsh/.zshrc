#!/usr/bin/env zsh

source "${HOME}/.zsh-things/.git.zsh"

# check if the user has sudoed recently and if not prompt for sudo pass
# to keep the sudo timestamp up to date
function check_sudo() {
    if [[ $(sudo -n uptime 2>&1|grep "load"|wc -l) -eq 0 ]]; then
        sudo -v
    fi
}
function apt-update-upgrade() {
    check_sudo
    ~/.spinner sudo apt update -qq 2>/dev/null
    ~/.spinner sudo apt upgrade -qqy 2>/dev/null
}

source "${HOME}/.zsh-things/.aliases.zsh"
