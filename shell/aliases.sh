function coffee() {
  sudo apt update -qq
  sudo apt upgrade -qqy
  sudo apt autoremove -qqy
  sudo apt autoclean
}

function install() {
  sudo apt update -qq
  sudo apt install $@
}

alias gcl="$(which python) ~/.shell/clone_repository.py"
alias browse="$(which python) ~/.shell/open_repository_in_browser.py"
alias ls="ls --color=auto"

function cs() {
  cd "$1" && ls
}

alias ..='cs ..'
alias ...='cs ../..'
alias ....='cs ../../..'
alias .....='cs ../../../..'
alias ......='cs ../../../../..'
alias .......='cs ../../../../../..'

alias sha1='openssl sha1'
alias sha256='openssl sha256'
alias sha512='openssl sha512'

alias gpl="git pull --rebase --autostash --prune"
alias gps="git push"
alias gpsf="git push --force-with-lease"

get_prompt_parts() {
  local python=$(which python)
  local hostname_part=$(python ~/.shell/hostname.py)
  local pathname_part=$(python ~/.shell/pathname.py)
  echo "${hostname_part} ${pathname_part} "
}

export PS1='$(get_prompt_parts)'
