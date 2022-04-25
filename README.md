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

### 1Password

Installs both `1password` and `1password-cli` - then configures the cli using
the variables from the vault. This saves me having to do any user input when I
want to get things like a gitlab token. Also means I can easily configure the
desktop app after install.

TODO: modify `~/.ssh/config` to reference the 1password agent socket

### Docker

Ensures that the latest version of `docker` and `docker compose` are installed.
Also logs me into the gitlab container registry.

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

Adds the signing key and repo then ensures on latest.

### Zsh

Includes zsh, oh-my-zsh, and some plugins to show icons for software that you
may or may not be using. Pretty clean. Constantly improving it. Should not slow
down your terminal by much (i.e. should be imperceptible).

Mostly just to make things pretty like adding icons to repo prompts.

### Git

Configures my global `.gitconfig` with sane defaults and switches my commit
email based on whether I'm in `~/gh/**` or `~/gl/**` (I wanted to change my git
commit email based on host, not directory, so this was a happy middle ground).

### Slack, Spotify

Installs the gpg keys along with repos for these packages then ensures the
`latest` version is installed.

### Discord

Similar to the above but it just grabs the `.deb` and installs it since Discord
shamefully doesn't have a repo. What's up with that, Discord? Can't even check
the signature of the `.deb` :sadface:.
