if command -v uv >/dev/null 2>&1; then
  freckles_python() { uv run --no-project "$@"; }
elif command -v python3 >/dev/null 2>&1; then
  freckles_python() { python3 "$@"; }
elif command -v python >/dev/null 2>&1; then
  freckles_python() { python "$@"; }
else
  freckles_python() {
    echo "Freckles helpers require either 'uv' or 'python3' in PATH." >&2
    return 127
  }
fi

freckles_python_quiet() {
  freckles_python "$@" 2>/dev/null
}

coffee() {
  sudo apt-get update -qq && \
  sudo apt-get upgrade -qqy && \
  sudo apt-get autoremove -qqy && \
  sudo apt-get autoclean
}

install() {
  sudo apt-get update -qq && sudo apt-get install -y "$@"
}

gcl() {
  freckles_python "$HOME/.shell/clone_repository.py" "$@"
}

browse() {
  freckles_python "$HOME/.shell/open_repository_in_browser.py" "$@"
}

dynamic_navigate() {
  freckles_python "$HOME/.shell/dynamic_navigate.py" "$@"
}

nn() {
    local target_dir status
    if [ $# -eq 0 ]; then
        target_dir=$(freckles_python_quiet "$HOME/.shell/dynamic_navigate.py")
        status=$?
    else
        target_dir=$(freckles_python_quiet "$HOME/.shell/dynamic_navigate.py" "$*")
        status=$?
    fi
    if [ $status -eq 0 ] && [ -n "$target_dir" ]; then
        cd "$target_dir" || echo "Failed to change directory"
    else
        echo "Failed to determine target directory"
        return $status
    fi
}

alias ls="ls --color=auto"
alias ll='ls -la'
alias l.='ls -d .* --color=auto'
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'

cs() {
  local target="${1:-$HOME}"
  cd "$target" || return $?
  ls
}

alias ..='cs ..'
alias ...='cs ../..'
alias ....='cs ../../..'
alias .....='cs ../../../..'
alias ......='cs ../../../../..'
alias .......='cs ../../../../../..'

alias c="clear"

alias sha1='openssl sha1'
alias sha256='openssl sha256'
alias sha512='openssl sha512'

alias gpl="git pull --rebase --autostash --prune"
alias gps="git push"
alias gpsf="git push --force-with-lease"
alias gfs="git fs"
alias grb="git rb"
alias gdb="git db"

if [ -f "$HOME/.cargo/env" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.cargo/env"
fi

if [ -d "$HOME/.bun/bin" ]; then
  export BUN_INSTALL="$HOME/.bun"
  export PATH="$BUN_INSTALL/bin:$PATH"
fi

export PYENV_ROOT="$HOME/.pyenv"
if [ -d "$PYENV_ROOT/bin" ]; then
  export PATH="$PYENV_ROOT/bin:$PATH"
fi
if command -v pyenv >/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi

export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  # shellcheck disable=SC1090
  . "$NVM_DIR/nvm.sh"
fi
if [ -s "$NVM_DIR/bash_completion" ]; then
  # shellcheck disable=SC1090
  . "$NVM_DIR/bash_completion"
fi

_freckles_prompt_segment() {
  local value
  value=$(freckles_python_quiet "$@");
  if [ $? -ne 0 ] || [ -z "$value" ]; then
    echo ""
  else
    echo "$value"
  fi
}

get_prompt_parts() {
  local hostname_part pathname_part git_branch_part endpart
  hostname_part=$(_freckles_prompt_segment "$HOME/.shell/hostname.py")
  if [ -z "$hostname_part" ]; then
    hostname_part="\u@\h"
  fi

  pathname_part=$(_freckles_prompt_segment "$HOME/.shell/pathname.py")
  if [ -z "$pathname_part" ]; then
    pathname_part="\w"
  fi

  git_branch_part=$(_freckles_prompt_segment "$HOME/.shell/gitname.py")
  endpart=$(_freckles_prompt_segment "$HOME/.shell/endpart.py")
  if [ -z "$endpart" ]; then
    endpart="\n» "
  fi

  echo "${hostname_part} ${pathname_part} ${git_branch_part}${endpart}"
}

export PS1='$(get_prompt_parts)'
