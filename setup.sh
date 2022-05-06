#!/usr/bin/env bash

set -e

ROOT=$(cd $(dirname $BASH_SOURCE[0]) && pwd);

if ! [ -x "$(command -v ansible)" ]; then
  echo "Do not have ansible. Installing..."

  # use AU sources
  sudo sed -i 's|http://us.|http://au.|' /etc/apt/sources.list.d/system.sources

  # update
  sudo apt update

  # upgrade
  sudo apt upgrade -y

  # install tools needed to build ansible
  sudo apt install software-properties-common python3-pip -y

  # alias python and pip
  alias python='python3'
  alias pip='pip3'

  # install ansible
  sudo pip install ansible black psutil pexpect --quiet
else
  echo "Already have ansible!"
fi

# run the playbook
ansible-playbook -i "$ROOT/hosts" "$ROOT/freckles.yml" --ask-become-pass --ask-vault-pass
