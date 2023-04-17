#!/bin/bash

function cursorBack() {
  echo -en "\033[$1D"
}

spinner() {
  local LC_CTYPE=C
  local charWidth=3
  local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
  local pid="${1}"
  local i=0
  tput civis
  while ps a | awk '{print $1}' | grep -q "${pid}"; do
    local i=$(((i + $charWidth) % ${#spin}))
    printf "\r%s" " ${spinner_icon} ${spin:$i:$charWidth} ${spinner_msg}"
    cursorBack 1
    sleep .1
  done
  printf "\r \e[92m${spinner_icon} ⠿ ${spinner_msg}OK\e[0m\r\n"
  tput cnorm
}

("$@") >/dev/null &

spinner $!
