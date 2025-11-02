# Freckles

Freckles are alexogeny's dotfiles.

Mostly hand-rolled bash scripts for intalling and configuring my system.

```shell
./setup.sh
```

## Some Notes

- only really works on linux. haven't really tested on macos or wsl
- currently supports Debian and Ubuntu Linux distributions
- is opinionated, like me

## Features

- installs and configures zsh with `--zsh`
- installs and configures vscode (including extensions) with `--vscode`
- installs and configures git, including both my personal and work configs with `--git`
  - ships helper aliases like `git fs` for a clean branch reset, `git rb` for
    remote branch discovery, and `git db` for default-branch detection
- onboarding walks through each git identity (personal, work, etc.), saves the
  answers, and keeps the includes in sync with future edits
  - provisions a shared SSH key for all identities and prints the public key
    ready to paste into GitHub/GitLab
  - generates and exports shared GPG signing material alongside the SSH key so
    everything stays in sync
  - see [Git Identity Concierge Guide](docs/git-identity-concierge.md) for
    manual onboarding steps or recovery when metadata needs to be created or
    fixed
- installs and configures brew with `--brew`
  - python 3 is installed with brew and set as the default python interpreter
  - node is installed with brew
  - bun is installed with brew
- installs docker with `--docker`
  - a bit janky, but that's just docker for you
- installs noisetorch with `--noisetorch` (linux only)
- installs slack, discord, spotify, plus the 1Password desktop app and CLI
- applies custom Firefox enterprise policies and profile defaults for a fast,
  privacy-friendly browser (memory-only cache, VR disabled, telemetry blocked)
- configures ssh with `--ssh`
  - uses a shared SSH key for all configured identities
  - exports public SSH/GPG material without editing existing 1Password vault items
  - uses .zshrc to set up ssh-agent on login
- includes a fuzzy `nn` navigator that understands relative paths, "-" for the
  previous directory, and smart tilde expansion
- turns off swap

Ubuntu specific:

- removes snap
- replaces firefox snap with direct binary install

### Firefox configuration templates

Firefox is now managed through templates in `firefox/policies.json` and
`firefox/user.js`. Rerun `setup.py` at any time to reapply these files and
restore the curated performance defaults. Edit the templates directly if you
want to tweak caching behaviour, enable specific features, or relax any of the
locked preferences.

## TODO

Just a general list of things I want to do with this project. I may or may not actually do them.

- [ ] add support for a $user.json file that can be used to configure the system instead of just using my own config
- [ ] add support for macos
- [ ] add support for wsl


popping these here for later

```shell
flatpak remote-delete flathub
flatpak repair --user
sudo apt remove --purge "libreoffice*"
sudo apt autoremove
sudo apt autoclean
```
