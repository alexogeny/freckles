#!/usr/bin/env bash

set -e

ROOT=$(cd $(dirname $BASH_SOURCE[0]) && pwd)

if which ansible; then
  echo 'already have ansible'
else
  sudo apt update && sudo apt install software-properties-common ansible python3-pip -y
fi

alias python='python3'
alias pip='pip3'

ansible-playbook -i "$ROOT/hosts" "$ROOT/freckles.yml" --ask-become-pass --ask-vault-pass
