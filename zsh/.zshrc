#!/usr/bin/env zsh

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

source "${HOME}/.zsh-things/git.zsh"
source "${HOME}/.zsh-things/aliases.zsh"
source "${HOME}/.zsh-things/python.zsh"
source "${HOME}/.zsh-things/node.zsh"
