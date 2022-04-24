#!/usr/bin/env zsh

: ${PACKAGE_PREFIX:=" "}
: ${PACKAGE_SUFFIX:=""}

typeset -g package_icon=""

function get_package_icon() {
  package_icon=""
  if (( $is_git )); then
    has_package="$(git rev-parse --show-toplevel)/package.json"
    if [ -f $has_package ]; then
      which jq > /dev/null
      if [ $? -eq 0 ]; then
        version_number="$(cat $has_package | jq .version | grep -Po '[0-9a-z\.]+')"
        if [[ ! $version_number =~ null ]]; then
          package_icon="${PACKAGE_PREFIX}%F{137}📦 ${version_number}%f${PACKAGE_SUFFIX}"
        fi
      fi
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd get_package_icon
get_package_icon
