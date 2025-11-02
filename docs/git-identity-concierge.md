# Git Identity Concierge Guide

This guide documents the end-to-end process for onboarding a git identity so
that SSH access, commit signing, and 1Password storage all stay in sync. It is
written for identities managed through the Freckles onboarding flow.

> **Note**
> Running `freckles configure git` followed by `freckles configure ssh` now
> generates missing SSH/GPG keys, imports existing material from 1Password when
> present, and prints the public data to paste into GitHub/GitLab. The checklist
> below remains a reference for manual recovery or environments where the
> automation cannot run.

## 1. Gather prerequisites

1. Ensure the 1Password CLI (`op`) is installed and authenticated (`op signin`).
2. Confirm that you know which Freckles git identity you are updating. You will
   need the alias slug (for example `personal-github` or `airev-gitlab`).
3. Locate the matching 1Password item that stores metadata for this account.
   The Freckles scripts expect an item per identity with the vault/item names
   recorded in `~/.config/freckles/accounts.json`.

## 2. Generate or import the SSH key material

1. Decide whether you are creating a new SSH key or importing an existing one.
2. For a new key, run:

   ```bash
   ssh-keygen -t ed25519 -C "<email-for-the-identity>" -f ~/.ssh/<alias>
   ```

   Replace `<alias>` with something recognisable (e.g. `airev-gitlab`).
3. If you already have a key, locate the private key (`id_ed25519`) and the
   matching public key (`id_ed25519.pub`).
4. Store the keys in `~/.ssh/`. Use `chmod 600` on the private key and
   `chmod 644` on the public key if needed.

## 3. Upload the SSH key to GitLab

1. Copy the contents of the public key file:

   ```bash
   cat ~/.ssh/<alias>.pub | pbcopy   # or use xclip/wl-copy on Linux
   ```

2. Navigate to **GitLab → User Settings → SSH Keys**.
3. Paste the public key, give it a descriptive title (e.g. `alex@laptop`), and
   save.
4. Verify SSH connectivity:

   ```bash
   ssh -T git@gitlab.com
   ```

   You should see a success greeting referencing your GitLab username.

## 4. Persist the SSH key in 1Password

1. Open the relevant 1Password item (for example `AI-Rev.net/gitlab token`).
2. Add or update the following fields:

   | Section | Field name     | Content                               |
   |---------|----------------|----------------------------------------|
   | `ssh`   | `private`      | The full private key block             |
   | `ssh`   | `public`       | The SSH public key copied in step 3    |
   | `ssh`   | `fingerprint`  | Output of `ssh-keygen -lf ~/.ssh/<alias>.pub` |

   If the `ssh` section does not exist, create it as a new section first.
3. Save the item. The Freckles tooling will now find `ssh.public` when it
   provisions SSH config files.

## 5. Configure commit signing (GPG)

1. Check whether a GPG key already exists for the identity:

   ```bash
   gpg --list-secret-keys --keyid-format LONG "<email-for-the-identity>"
   ```

2. If you need to create a new key:

   ```bash
   gpg --full-generate-key
   ```

   - Choose **(1) RSA and RSA** or **(4) EdDSA and Ed25519**.
   - Use at least a 4096-bit RSA key if selecting RSA.
   - Set the uid email address to match the git identity.
3. After generation, grab the long key ID:

   ```bash
   gpg --list-secret-keys --keyid-format LONG "<email>"
   ```

   The key ID is the hex string after `sec   rsa4096/`.
4. Export the ASCII-armored public key and add it to GitLab under
   **User Settings → GPG Keys**:

   ```bash
   gpg --armor --export <KEY_ID> | pbcopy
   ```

5. Back in 1Password, add the following fields to the same identity item (or a
   linked item if preferred):

   | Section | Field name | Content                                    |
   |---------|------------|---------------------------------------------|
   | `gpg`   | `public`   | The ASCII-armored public key                |
   | `gpg`   | `private`  | Output of `gpg --armor --export-secret-keys <KEY_ID>` |
   | `gpg`   | `key_id`   | The long key ID (e.g. `ABCDEF1234567890`)   |

   Mark the private key field as “concealed” in 1Password.
6. Update the Freckles git account configuration (`freckles configure git`) so
   that the `signing_key` value for the identity matches `<KEY_ID>`.

## 6. Refresh Freckles-managed configuration

1. Run the Freckles git configuration helper:

   ```bash
   freckles configure git
   ```

2. Confirm that `~/.gitconfig` now includes lines similar to:

   ```ini
   [includeIf "gitdir:~/airev/gitlab/**/.git"]
     path = ~/.airev-gitlab.gitconfig
   ```

3. Inspect the generated per-identity file (`~/.airev-gitlab.gitconfig`) to
   ensure it carries the expected `[user]` block (and `[github]` section when
   applicable).
4. Verify commit signing:

   ```bash
   git config --global user.signingkey
   git commit -S --allow-empty -m "verify signing"
   ```

   Then check the commit in GitLab/GitHub to ensure it is marked as verified.

Following this checklist keeps GitLab, 1Password, and the Freckles automation in
sync for each alias, preventing missing-field errors such as the `ssh.public`
lookup failure.
