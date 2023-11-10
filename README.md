# Freckles

Freckles are alexogeny's dotfiles.

Mostly hand-rolled bash scripts for intalling and configuring my system.

```shell
./setup.sh
```

## Some Notes

- only really works on linux. haven't really tested on macos or wsl
- currently only supports debian flavors of linux
- is opinionated, like me

## Features

- installs and configures zsh with `--zsh`
- installs and configures vscode (including extensions) with `--vscode`
- installs and configures git, including both my personal and work configs with `--git`
- installs and configures brew with `--brew`
  - python 3 is installed with brew and set as the default python interpreter
  - node is installed with brew
  - bun is installed with brew
- installs docker with `--docker`
  - a bit janky, but that's just docker for you
- installs noisetorch with `--noisetorch` (linux only)
- installs slack, discord, and spotify
- configures ssh with `--ssh`
  - uses 1password to retrieve ssh keys
  - uses .zshrc to set up ssh-agent on login
- turns off swap

Ubuntu specific:

- removes snap
- replaces firefox snap with direct binary install

## TODO

Just a general list of things I want to do with this project. I may or may not actually do them.

- [ ] add support for a $user.json file that can be used to configure the system instead of just using my own config
- [ ] add support for macos
- [ ] add support for wsl
