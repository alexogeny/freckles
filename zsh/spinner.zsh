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
    sleep .08
  done

  # Wait for the command to finish and get its exit status
  local exit_status
  wait "${pid}"
  exit_status=$?

  if [ $exit_status -eq 0 ]; then
    printf "\r \e[92m${spinner_icon} ⠿ ${spinner_msg} OK\e[0m\r\n"
  else
    printf "\r \e[91m${spinner_icon} ⠿ ${spinner_msg} ERROR\e[0m\r\n"
    printf "\e[31m$(cat "${tmp_file}")\e[0m\r\n"
  fi
  tput cnorm
}

# Create a temporary file to store the error output
tmp_file=$(mktemp)
# Redirect both stdout and stderr to their respective files
("$@" 1>/dev/null 2>"${tmp_file}") &

spinner $!

# Clean up the temporary file
rm -f "${tmp_file}"
