# Freckles

Freckles are alexogny's dotfiles.

I haven't done much with the setup script yet, but the `run.sh` script will at
least do the popos cleanups and install vscode extensions.

Hope to make it more robust later.

## Popos cleanups

Does some cleanups after installing pop os. Namely it:
- cleans up libre office (since I do not use it)
- removes unused locales

## Firefox

`lockedConfig.js` are all the preferences I use in firefox to harden it.
These preferences are loaded by usage of autoconfig.js and firefox.cfg

A bunch of these changes will break sites but I figure the tradeoff is worth it.

## Vscode

Includes keybindings, settings (preferences), and a list of extensions that I
use during my day to day experience (intellisense, graphql, convert case, etc.)

## TODO: zsh and zshrc
