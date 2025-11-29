from __future__ import annotations

from pathlib import Path

from freckles.identity.accounts import GitAccount
from freckles import ssh


def sample_account() -> GitAccount:
    return GitAccount(
        scope="work",
        provider="github",
        display_name="Freckles",
        email="freckles@example.com",
        directory="~/work/github",
    )


def test_ensure_config_entry_appends_new_block(tmp_path):
    account = sample_account()
    identity = tmp_path / "id_rsa"
    identity.write_text("key")
    updated, changed = ssh._ensure_config_entry(account, "", identity_file=identity)
    assert changed is True
    assert f"Host {account.ssh_alias}" in updated
    assert identity.as_posix()[:5] not in updated  # path should be normalised with ~


def test_ensure_config_entry_upgrades_identity(tmp_path):
    account = sample_account()
    wrong_identity = tmp_path / "old"
    wrong_identity.write_text("old")
    identity = tmp_path / "new"
    identity.write_text("new")

    existing = f"Host {account.ssh_alias}\n    IdentityFile {wrong_identity}\n"
    updated, changed = ssh._ensure_config_entry(account, existing, identity_file=identity)
    assert changed is True
    assert ssh._format_identity_path(identity) in updated
