#!/usr/bin/env zsh

: ${YARN_PREFIX:=" "}
: ${YARN_SUFFIX:=""}

typeset -g yarn_icon=""

function get_yarn_icon() {
  yarn_icon=""
  if (( $is_git )); then
    has_yarn="$(git rev-parse --show-toplevel)/yarn.lock"
    if [ -f $has_yarn ]; then
      yarn_icon="${YARN_PREFIX}%F{161}🧶 yarn%f${YARN_SUFFIX}"
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd get_yarn_icon
get_yarn_icon
