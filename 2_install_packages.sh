#!/bin/bash

sudo apt-get update

packages=(
    nginx
    git
    curl
    build-essential
    libbz2-dev
    cargo
    libsqlite3-dev
    ca-certificates
)

to_install=()

for package in "${packages[@]}"; do
    if dpkg -l | grep -q "^ii  $package"; then
        echo "$package is already installed."
    else
        echo "$package is not installed. It will be added to the install list."
        to_install+=("$package")
    fi
done

if [ ${#to_install[@]} -eq 0 ]; then
    echo "All packages are already installed."
else
    echo "Installing packages: ${to_install[*]}"
    sudo apt-get install -y "${to_install[@]}"

    for package in "${to_install[@]}"; do
        if dpkg -l | grep -q "^ii  $package"; then
            echo "$package was installed successfully."
        else
            echo "Failed to install $package."
        fi
    done
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -sSfL https://astral.sh/uv/install.sh | bash
  if [ ! -d "$HOME/.local/bin/ruff" ]; then
    "$HOME/.cargo/bin/uv" tool install ruff
    "$HOME/.cargo/bin/uv" tool install ruff-lsp
  fi
  if [ ! -d "$HOME/.local/bin/pipenv" ]; then
    "$HOME/.cargo/bin/uv" tool install pipenv
  fi
fi

if ! command -v bun >/dev/null 2>&1; then
  curl -fsSL https://bun.sh/install | bash
fi

if ! command -v docker >/dev/null 2>&1; then
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL "https://download.docker.com/linux/debian/gpg" -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt update
  DEBIAN_FRONTEND=noninteractive sudo apt install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-ce-rootless-extras docker-buildx-plugin >/dev/null
  if ! getent group docker > /dev/null; then
    sudo groupadd docker
  fi
  sudo usermod -aG docker $USER
  newgrp docker
  docker run hello-world
fi

if ! command -v noisetorch >/dev/null 2>&1; then
  RELEASES_URL="https://api.github.com/repos/noisetorch/NoiseTorch/releases/latest"
  RELEASE_DATA=$(curl -s $RELEASES_URL)
  ASSET_URL=$(echo $RELEASE_DATA | jq -r '.assets[] | select(.name | test(".tgz$")) | .browser_download_url')
  CHECKSUM=$(echo $RELEASE_DATA | jq -r '.assets[] | select(.name | test("sha512sum")) | .browser_download_url')

  if [ -z "$ASSET_URL" ] || [ -z "$CHECKSUM" ]; then
    exit 1
  fi
  curl -L -o noisetorch-x64.tar.gz $ASSET_URL
  curl -L -o noisetorch-x64.sha512sum $CHECKSUM
  read -r CHECKSUM_FILE CHECKSUM_FILE_NAME <<<$(cat noisetorch-x64.sha512sum)
  CHECKSUM_CALCULATED=$(sha512sum noisetorch-x64.tar.gz | awk '{print $1}')
  if [ "$CHECKSUM_FILE" != "$CHECKSUM_CALCULATED" ]; then
    exit 1
  fi
  tar -C $HOME -h -xzf noisetorch-x64.tar.gz
  gtk-update-icon-cache
  sudo setcap 'CAP_SYS_RESOURCE=+ep' "$HOME/.local/bin/noisetorch"
  rm -f noisetorch-x64.tar.gz noisetorch-x64.sha512sum
fi
