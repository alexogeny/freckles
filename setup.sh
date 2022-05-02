#!/usr/bin/env bash

set -e

ROOT=$(cd $(dirname $BASH_SOURCE[0]) && pwd)

sudo apt update && sudo apt install software-properties-common python3-pip -y

alias python='python3'
alias pip='pip3'

sudo pip install ansible black pexpect --quiet

ansible-playbook -i "$ROOT/hosts" "$ROOT/freckles.yml" --ask-become-pass --ask-vault-pass
