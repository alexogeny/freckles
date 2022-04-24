#!/usr/bin/env zsh

: ${TS_PREFIX:=" "}
: ${TS_SUFFIX:=""}

typeset -g typescript_icon=""

function get_typescript_icon() {
  typescript_icon=""
  if (( $is_git )); then
    has_tsconfig="$(git rev-parse --show-toplevel)/tsconfig.json"
    if [ -f $has_tsconfig ]; then
      typescript_icon="${TS_PREFIX}%F{060}🧷 typescript%f${TS_SUFFIX}"
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd get_typescript_icon
get_typescript_icon
