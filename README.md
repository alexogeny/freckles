# Freckles

Freckles are alexogeny's dotfiles.

Built using ansible. To run:

```shell
sh setup.sh
```

## Important Notes

**SYMLINKS** - Keep in mind that this will do symlinks to this folder, and it
WILL override existing config files. Make sure to back up files you might want
to keep and also run the script from a place where you won't be moving the
 repository.

**OS SUPPORT** - This will likely only work on popos (and maybe vanilla debian).
Will likely not work on the latest Ubuntu due to the abomination that is `snapd`
but anything before `22.04` should work (mostly due to the hijacking of `apt
install firefox` being redirected to `snap install` without the user's consent).

### Firefox

`lockedConfig.js` are all the preferences I use in firefox to harden it.
These preferences are loaded by usage of autoconfig.js and firefox.cfg. The
autoload file references the `lockedConfig.js` in the GitHub cloud, so I can
make changes on the fly and not have to redo any setup.

A bunch of these changes will break sites but I figure the tradeoff is worth it.

Keep an extra ungoogled chromium if you need to access anything that's broken.

### Vscode

Includes keybindings, settings (preferences), and a list of extensions that I
use during my day to day experience (intellisense, graphql, convert case, etc.)

They're all pretty useful, but feel free to add or remove extensions from the
list.

### Zsh

Includes zsh, oh-my-zsh, and some plugins to show icons for software that you
may or may not be using. Pretty clean. Constantly improving it. Should not slow
down your terminal by much (i.e. should be imperceptible).

### TODO: automagic git configuration
