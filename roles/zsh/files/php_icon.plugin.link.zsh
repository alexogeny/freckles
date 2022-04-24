#!/usr/bin/env zsh

: ${PHP_PREFIX:=" "}
: ${PHP_SUFFIX:=""}

typeset -g php_icon=""

function get_php_icon() {
  php_icon=""
  if (( $is_git )); then
    has_composer="$(git rev-parse --show-toplevel)/composer.json"
    if [ -f $has_composer ]; then
      which jq > /dev/null
      if [ $? -eq 0 ]; then
        versionNumber="$(cat $has_composer | jq .require.php | grep -Po '[0-9a-z\.]+')"
        php_icon="${PHP_PREFIX}%F{147}🐘 php ${versionNumber}%f${PHP_SUFFIX}"
      else
        php_icon="${PHP_PREFIX}%F{147}🐘 php%f${PHP_SUFFIX}"
      fi
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd get_php_icon
get_php_icon
