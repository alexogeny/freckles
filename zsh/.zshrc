#!/usr/bin/env zsh

# set up ssh agent
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
fi

# colors
blue='%F{045}'
green='%F{077}'
purple='%F{141}'
orange='%F{208}'
red='%F{203}'
pink='%F{219}'

eval "$(ssh-agent -s)" >/dev/null 2>&1
for service in "github" "gitlab"; do
    for vault in "personal" "work"; do
        priv_key="${service}.${vault}"
        if [ -f "${HOME}/.ssh/${priv_key}" ]; then
            ssh-add "${HOME}/.ssh/${priv_key}" >/dev/null 2>&1
        fi
    done
done

function check_sudo() {
    if [[ $(sudo -n uptime 2>&1|grep "load"|wc -l) -eq 0 ]]; then
        sudo -v
    fi
}

function apt-update-upgrade() {
    check_sudo
    export spinner_icon="📦"
    export spinner_msg="Updating apt"
    ~/.spinner sudo apt update -qq
    export spinner_icon="📦"
    export spinner_msg="Installing apt upgrades"
    ~/.spinner sudo apt upgrade -qqy
}

function apt-install() {
    check_sudo
    export spinner_icon="📦"
    export spinner_msg="Installing $@"
    ~/.spinner sudo apt install -qqy "$@"
}

source "${HOME}/.zsh-things/git.zsh"
source "${HOME}/.zsh-things/aliases.zsh"
source "${HOME}/.zsh-things/python.zsh"
source "${HOME}/.zsh-things/node.zsh"
source "${HOME}/.zsh-things/rust.zsh"
