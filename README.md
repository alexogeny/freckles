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

### Zsh

Includes zsh, and some plugins to show icons for software that you
may or may not be using. Pretty clean. Constantly improving it. Should not slow
down your terminal by much (i.e. should be imperceptible).

### Git

Configures my global `.gitconfig` with sane defaults and switches my commit
email based on whether I'm `~/Work/**` or `~/Personal/**` (I wanted to change my git
commit email based on host, not directory, so this was a happy middle ground).

Then it checks whether in Github or Gitlab folder and uses relevant ssh key
accordingly.
