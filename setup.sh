#!/usr/bin/env bash

set -e

ROOT=$(cd $(dirname $BASH_SOURCE[0]) && pwd)

has_ansible=$(which ansible > /dev/null 2>&1)

$has_ansible || sudo apt update
$has_ansible || sudo apt install software-properties-common python3-pip -y
$has_ansible && echo "You already have ansible. Nice!"

alias python='python3'
alias pip='pip3'

$has_ansible || sudo pip install ansible black psutil pexpect --quiet

ansible-playbook -i "$ROOT/hosts" "$ROOT/freckles.yml" --ask-become-pass --ask-vault-pass
