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

alias gcl="uv run --no-project ~/.shell/clone_repository.py"
alias browse="uv run --no-project ~/.shell/open_repository_in_browser.py"
alias dynamic_navigate="uv run --no-project ~/.shell/dynamic_navigate.py"
function nn() {
    local target_dir=$(uv run --no-project ~/.shell/dynamic_navigate.py "$1")
    if [ -n "$target_dir" ]; then
        cd "$target_dir" || echo "Failed to change directory"
    else
        echo "Failed to determine target directory"
    fi
}
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

. "$HOME/.cargo/env"

export BUN_INSTALL="$HOME/.bun"
export PATH=$BUN_INSTALL/bin:$PATH
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

get_prompt_parts() {
  local hostname_part=$(uv run --no-project ~/.shell/hostname.py)
  local pathname_part=$(uv run --no-project ~/.shell/pathname.py)
  echo "${hostname_part} ${pathname_part} "
}

export PS1='$(get_prompt_parts)'
