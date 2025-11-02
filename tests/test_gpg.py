import sys
from subprocess import CompletedProcess

import pytest

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import gpg  # noqa: E402
from utils.accounts import AccountConfig, GitAccount  # noqa: E402


def _build_account():
    account = GitAccount(
        scope="work",
        provider="github",
        display_name="Example User",
        email="example@example.com",
        directory="~/work/example",
        op_vault="Vault",
        op_item="Item",
    )
    return account


def _placeholder_item():
    return {
        "fields": [
            {
                "label": "public",
                "section": {"label": "gpg"},
                "value": "@/tmp/freckles-op-placeholder",
            },
            {
                "label": "private",
                "section": {"label": "gpg"},
                "value": "@/tmp/freckles-op-placeholder",
            },
            {
                "label": "key_id",
                "section": {"label": "gpg"},
                "value": "",
            },
            {
                "label": "fingerprint",
                "section": {"label": "gpg"},
                "value": "",
            },
        ]
    }


def test_import_remote_key_ignores_placeholder(monkeypatch):
    account = _build_account()
    commands = []

    def fake_run(command: str):
        commands.append(command)
        return CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(gpg, "run", fake_run)

    assert gpg._import_remote_key(account, _placeholder_item()) is None
    assert commands == []


def test_provision_replaces_placeholder_fields(monkeypatch):
    account = _build_account()
    config = AccountConfig(accounts=[account], default_account=account.slug)

    key_id = "ABCDEF1234567890"
    fingerprint = "FINGERPRINT1234567890"

    item_payload = _placeholder_item()

    def fake_get_item(vault: str, item: str, suppress_missing: bool = False):
        assert vault == "Vault"
        assert item == "Item"
        return item_payload

    updated_fields = []

    def fake_update_item_fields(vault: str, item: str, fields):
        updated_fields.extend(fields)
        return True

    saved_configs = []

    def fake_save_account_config(value):
        saved_configs.append(value)

    commands = []

    def fake_run(command: str):
        commands.append(command)
        if "--generate-key" in command:
            pytest.fail("Unexpected request to generate a new GPG key")
        if command.startswith("gpg --list-secret-keys"):
            payload = (
                "sec:u:4096:1:ABCDEF1234567890:0:0:::\n"
                "fpr:::::::::FINGERPRINT1234567890:\n"
            )
            return CompletedProcess(args=command, returncode=0, stdout=payload, stderr="")
        if command.startswith("gpg --armor --export-secret-keys"):
            return CompletedProcess(args=command, returncode=0, stdout="PRIVATE-KEY\n", stderr="")
        if command.startswith("gpg --armor --export"):
            return CompletedProcess(args=command, returncode=0, stdout="PUBLIC-KEY\n", stderr="")
        if command.startswith("gpg --with-colons --fingerprint"):
            payload = (
                "sec:u:4096:1:ABCDEF1234567890:0:0:::\n"
                "fpr:::::::::FINGERPRINT1234567890:\n"
            )
            return CompletedProcess(args=command, returncode=0, stdout=payload, stderr="")
        return CompletedProcess(args=command, returncode=1, stdout="", stderr="unexpected command")

    monkeypatch.setattr(gpg, "run", fake_run)
    monkeypatch.setattr(gpg, "ensure_op_connected", lambda: None)
    monkeypatch.setattr(gpg, "get_item", fake_get_item)
    monkeypatch.setattr(gpg, "update_item_fields", fake_update_item_fields)
    monkeypatch.setattr(gpg, "save_account_config", fake_save_account_config)

    updates = gpg.provision_gpg_material(config)

    assert len(updates) == 1
    updated_account, material = updates[0]
    assert updated_account is account
    assert material.key_id == key_id
    assert material.fingerprint == fingerprint
    assert material.public_key == "PUBLIC-KEY"
    assert material.private_key == "PRIVATE-KEY"

    assert saved_configs and saved_configs[0] is config

    assert {field.label for field in updated_fields} == {
        "public",
        "private",
        "key_id",
        "fingerprint",
    }
    for field in updated_fields:
        assert not field.value.strip().startswith("@")

    assert any(cmd.startswith("gpg --armor --export ") for cmd in commands)
    assert any(cmd.startswith("gpg --armor --export-secret-keys ") for cmd in commands)
