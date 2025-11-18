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

kill_port_on_prompt() {
  if ! command -v lsof >/dev/null 2>&1; then
    echo "'lsof' is required for killport" >&2
    return 127
  fi

  if [ -z "$1" ]; then
    echo "Usage: killport <port>" >&2
    return 1
  fi

  local port="$1" pids
  pids=$(lsof -ti :"$port" 2>/dev/null | tr '\n' ' ')
  if [ -z "$pids" ]; then
    echo "No processes found on port $port"
    return 0
  fi

  echo "Processes listening on port $port:"
  lsof -i :"$port"
  printf "Kill process(es) %s? [y/N] " "$pids"
  read -r response
  case "$response" in
    y|Y|yes|YES)
      echo "$pids" | xargs -r kill -9
      ;;
    *)
      echo "Aborted"
      ;;
  esac
}
alias killport=kill_port_on_prompt

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

_freckles_sync_aws_profile() {
  local desired status
  desired=$(freckles_python_quiet "$HOME/.shell/aws_profile.py")
  status=$?
  if [ $status -ne 0 ]; then
    return
  fi

  if [ -z "$desired" ]; then
    if [ -n "$FRECKLES_AWS_PROFILE" ]; then
      unset FRECKLES_AWS_PROFILE
      unset AWS_PROFILE
      unset AWS_DEFAULT_PROFILE
      unset AWS_VAULT
    fi
    return
  fi

  if [ "$desired" != "$FRECKLES_AWS_PROFILE" ]; then
    export FRECKLES_AWS_PROFILE="$desired"
    export AWS_PROFILE="$desired"
    export AWS_DEFAULT_PROFILE="$desired"
    export AWS_VAULT="$desired"
  fi
}

if [ -n "${ZSH_VERSION-}" ]; then
  typeset -a precmd_functions
  found=0
  for fn in "${precmd_functions[@]}"; do
    if [ "$fn" = "_freckles_sync_aws_profile" ]; then
      found=1
      break
    fi
  done
  if [ $found -eq 0 ]; then
    precmd_functions=("${precmd_functions[@]}" "_freckles_sync_aws_profile")
  fi
else
  case ";$PROMPT_COMMAND;" in
    *"_freckles_sync_aws_profile"*) ;;
    *) PROMPT_COMMAND="_freckles_sync_aws_profile${PROMPT_COMMAND:+;$PROMPT_COMMAND}" ;;
  esac
fi
