#!/usr/bin/env zsh

: ${DC_PREFIX:=" "}
: ${DC_SUFFIX:=""}

typeset -g docker_icon=""

function get_docker_icon() {
  docker_icon=""
  if (( $is_git )); then
    has_dcompose="$(git rev-parse --show-toplevel)/docker-compose.yml"
    if [ -f $has_dcompose ]; then
      versionNumber="$(echo "${$(docker --version)//Docker version /}" | cut -d',' -f1)"
      subVersion="$(head -n 1 $has_dcompose | cut -d' ' -f2 | grep -Po '[0-9a-z\.]+')"
      docker_icon="${DC_PREFIX}%F{075}🐋 docker ${versionNumber} (${subVersion})%f${DC_SUFFIX}"
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd get_docker_icon
get_docker_icon
