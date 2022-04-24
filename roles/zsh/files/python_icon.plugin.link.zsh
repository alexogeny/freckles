#!/usr/bin/env zsh

: ${NODE_PREFIX:=" "}
: ${NODE_SUFFIX:=""}

typeset -g python_icon=""

function get_python_icon() {
  python_icon=""
  if (( $is_git )); then
    git_top_level=$(git rev-parse --show-toplevel)
    has_requirements_txt="$git_top_level/requirements.txt"
    has_pyproject_toml="$git_top_level/pyproject.toml"
    has_setup_py="$git_top_level/setup.py"
    if [[ -f $has_requirements_txt || -f $has_pyproject_toml || -f $has_setup_py ]]; then
      python_icon="${NODE_PREFIX}%F{220}🐍 python%f${NODE_SUFFIX}"
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd get_python_icon
get_python_icon
