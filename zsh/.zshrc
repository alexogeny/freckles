#!/usr/bin/env zsh

setopt promptsubst

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

function cache-clean() {
  check_sudo
  if command -v yarn >/dev/null 2>&1; then
    yarn cache clean
  fi
  if command -v pip >/dev/null 2>&1; then
    pip cache purge
  fi
  if command -v npm >/dev/null 2>&1; then
    npm cache clean --force
  fi
  sudo apt autoclean
  if [ -d ~/.cache/pip ]; then
    rm -rf ~/.cache/pip
  fi
  if [ -d ~/.cache/pip-tools ]; then
    rm -rf ~/.cache/pip-tools
  fi
  if [ -d ~/.bun/install/cache ]; then
    rm -rf ~/.bun/install/cache
  fi
}

function host-name() {
  echo -n "$pink%n$purple@$pink%m%f"
}

function path-name() {
  echo -n " $blue"
  local current_path=$(print -rD $PWD)
  truncate-path $current_path
}

function preexec() {
    timer=$(date +%s%3N)
}

function truncate-path() {
  local current_path=$1
  local prefix=''
  if [[ '~' = "${current_path:0:1}" ]]; then
    current_path=${current_path:1}
    prefix='~'
  fi
  IFS='/' read -rA dirs <<< $current_path
  if [[ ${#dirs} -gt 5 ]]; then
    slashes=$(printf "/%.0s" {1..$(((${#dirs}-4)))})
    fqp=$(printf "%s/%s/%s%s%s/%s" $prefix $dirs[2] $dirs[3] $slashes $dirs[-2] $dirs[-1])
  else
    fqp=$(printf "%s%s" $prefix $current_path)
  fi
  echo -n $fqp
}

function precmd() {
  if [ $timer ]; then
    local now=$(date +%s%3N)
    local d_ms=$(($now-$timer))
    local d_s=$((d_ms / 1000))
    local ms=$((d_ms % 1000))
    local s=$((d_s % 60))
    local m=$(((d_s / 60) % 60))
    local h=$((d_s / 3600))
    if ((h > 0)); then elapsed=${h}h${m}m
    elif ((m > 0)); then elapsed=${m}m${s}s
    elif ((s >= 10)); then elapsed=${s}.$((ms / 100))s
    elif ((s > 0)); then elapsed=${s}.$((ms / 10))s
    else elapsed=${ms}ms
    fi

    export RPROMPT="%F{cyan}${elapsed} %{$reset_color%}"
    unset timer
  fi
}

function prompt() {
    echo -n ' %(!.#.»)%f '
}

function nl() {
    echo -n '\n'
}

source "${HOME}/.zsh-things/git.zsh"
source "${HOME}/.zsh-things/aliases.zsh"
source "${HOME}/.zsh-things/python.zsh"
source "${HOME}/.zsh-things/node.zsh"
source "${HOME}/.zsh-things/rust.zsh"

final-prompt() {
    host-name
    path-name
    prompt
}

PROMPT='$(final-prompt)'

export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
