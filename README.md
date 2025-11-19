# Freckles

Freckles are alexogeny's dotfiles and workstation bootstrap scripts.

Everything is orchestrated by a Python setup script. With [uv](https://github.com/astral-sh/uv)
installed, provisioning a machine is as simple as:

```shell
uv run setup.py
```

## Some Notes

- only really works on linux. haven't really tested on macos or wsl
- currently supports Debian and Ubuntu Linux distributions
- is opinionated, like me

## Features

- installs required base tooling including curl, git, make, zsh, and the Cascadia
  Code font so prompts, editors, and terminals share the same typography
- configures zsh, syncs the custom freckles prompt, and ensures aliases and
  helper scripts are available from both bash and zsh
- installs Visual Studio Code, applies the bespoke **Freckles Midnight/Dawn**
  themes, and keeps curated settings and keybindings in sync
- applies opinionated GNOME desktop defaults (dark appearance, Adwaita theming,
  Night Light, sensible keyboard shortcuts) and configures GNOME Terminal with
  the Freckles palette, cursor, and sizing
- installs and configures git, including both personal and work identities,
  helper aliases like `git fs`/`git rb`, and the shared SSH/GPG material used by
  [git identity concierge](docs/git-identity-concierge.md)
- provisions Firefox with enterprise policies, curated defaults, and add-ons
- installs 1Password, Slack, Spotify, Docker Engine (with Compose), and the 1Password CLI directly from their
  upstream repositories (adds your user to the `docker` group automatically—log out/in after setup)
- syncs the freckles shell helpers such as the fuzzy `nn` navigator and keeps
  the workstation ready for daily development

### Terminal experience

Provisioning now uses a lightweight CLI spinner for sub-commands and an inline
GNOME/TTY dashboard while `setup.py` runs. The dashboard keeps the checklist of
phases pinned to the top of the terminal and streams contextual log lines for
the active task beneath it (similar to Docker builds). When running in a
non-interactive environment the legacy log stream remains available.

Ubuntu specific:

- removes snap
- replaces firefox snap with direct binary install

### Firefox configuration templates

Firefox is now managed through templates in `firefox/policies.json` and
`firefox/user.js`. Rerun `setup.py` at any time to reapply these files and
restore the curated performance defaults. Edit the templates directly if you
want to tweak caching behaviour, enable specific features, or relax any of the
locked preferences.

## Development

Install [uv](https://github.com/astral-sh/uv) and then run:

```shell
uv run python -m pytest
```

That command exercises the spinner, SSH config helpers, reporter dashboard, and
GNOME automation logic. Use `uv run setup.py -- --help` to inspect the CLI,
and see `docs/` for subsystem-specific details.

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
