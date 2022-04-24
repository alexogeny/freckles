#!/usr/bin/env bash

set -e

ROOT=$(cd $(dirname $BASH_SOURCE[0]) && pwd)

if which ansible; then
  echo 'already have ansible'
else
  sudo apt update && sudo apt install software-properties-common ansible -y
fi

ansible-playbook -i "$ROOT/hosts" "$ROOT/freckles.yml" --ask-become-pass -vv
