#!/usr/bin/env zsh

source "${HOME}/.zsh-things/.git.zsh"

# function to run apt update and upgrade
function apt-update-upgrade() {
    ~/.spinner sudo apt update -qq 2>/dev/null
    ~/.spinner sudo apt upgrade -qqy 2>/dev/null
}
alias auu="apt-update-upgrade"

alias cdw="cd ~/Work"
alias cdp="cd ~/Personal"
