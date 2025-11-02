"""Helpers to provision and export GPG material for git identities."""

from __future__ import annotations

import shlex
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .accounts import AccountConfig, GitAccount, save_account_config
from .debian import run
from .one_password import (
    OnePasswordField,
    ensure_op_connected,
    get_field_value,
    get_item,
    update_item_fields,
)


@dataclass
class GpgMaterial:
    """Container for exported GPG key material."""

    key_id: str
    fingerprint: str
    public_key: str
    private_key: str


def _parse_secret_key(output: str) -> Optional[Tuple[str, str]]:
    """Extract the key id and fingerprint from ``gpg --with-colons`` output."""

    key_id: Optional[str] = None
    fingerprint: Optional[str] = None
    for line in output.splitlines():
        parts = line.split(":")
        if not parts:
            continue
        record_type = parts[0]
        if record_type == "sec" and len(parts) > 4:
            key_id = parts[4]
        elif record_type == "fpr" and len(parts) > 9 and fingerprint is None:
            fingerprint = parts[9]
    if key_id and fingerprint:
        return key_id, fingerprint
    if key_id:
        return key_id, ""
    return None


def _discover_existing_key(account: GitAccount) -> Optional[Tuple[str, str]]:
    result = run(
        f'gpg --list-secret-keys --with-colons --fingerprint "{account.email}"'
    )
    if result.returncode != 0:
        return None
    return _parse_secret_key(result.stdout or "")


def _import_remote_key(account: GitAccount, item: Optional[Dict]) -> Optional[Tuple[str, str]]:
    if not item:
        return None

    private_key = get_field_value(item, "gpg", "private") or ""
    if not private_key.strip():
        return None

    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(private_key.strip() + "\n")

    try:
        result = run(f"gpg --batch --import {shlex.quote(temp_path.as_posix())}")
    finally:
        temp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(
            f"Failed to import GPG key for {account.display_name} "
            f"({account.email}) from 1Password: {message}"
        )
        return None

    return _discover_existing_key(account)


def _generate_key(account: GitAccount) -> Optional[Tuple[str, str]]:
    template = """
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
%no-protection
%commit
""".strip().format(name=account.display_name, email=account.email)

    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        template_path = Path(handle.name)
        handle.write(template)

    command = f"gpg --batch --generate-key {shlex.quote(template_path.as_posix())}"
    result = run(command)
    template_path.unlink(missing_ok=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(
            f"Failed to generate GPG key for {account.display_name} "
            f"({account.email}): {message}"
        )
        return None

    return _discover_existing_key(account)


def _export_material(key_id: str) -> Optional[GpgMaterial]:
    public_result = run(f"gpg --armor --export {key_id}")
    if public_result.returncode != 0:
        message = public_result.stderr.strip() or public_result.stdout.strip() or "unknown error"
        print(f"Failed to export public GPG key {key_id}: {message}")
        return None

    private_result = run(f"gpg --armor --export-secret-keys {key_id}")
    if private_result.returncode != 0:
        message = private_result.stderr.strip() or private_result.stdout.strip() or "unknown error"
        print(f"Failed to export private GPG key {key_id}: {message}")
        return None

    fingerprint_result = run(
        f"gpg --with-colons --fingerprint {key_id}"
    )
    fingerprint = ""
    if fingerprint_result.returncode == 0:
        parsed = _parse_secret_key(fingerprint_result.stdout or "")
        if parsed:
            fingerprint = parsed[1]

    return GpgMaterial(
        key_id=key_id,
        fingerprint=fingerprint,
        public_key=(public_result.stdout or "").strip(),
        private_key=(private_result.stdout or "").strip(),
    )


def _needs_update(item: Optional[Dict], field: str) -> bool:
    if not item:
        return True
    value = get_field_value(item, "gpg", field)
    return not value


def provision_gpg_material(config: AccountConfig) -> List[Tuple[GitAccount, GpgMaterial]]:
    """Ensure each account has exported GPG material stored in 1Password."""

    eligible_accounts = [
        account
        for account in config.accounts
        if account.op_vault and account.op_item
    ]
    if not eligible_accounts:
        return []

    ensure_op_connected()
    updated_material: List[Tuple[GitAccount, GpgMaterial]] = []
    config_updated = False

    for account in eligible_accounts:
        item = get_item(account.op_vault, account.op_item, suppress_missing=True)
        remote_private = (get_field_value(item, "gpg", "private") or "") if item else ""
        details = _discover_existing_key(account)
        generated_new_key = False
        if details is None and remote_private.strip():
            details = _import_remote_key(account, item)
            if details is None:
                continue
        if details is None:
            details = _generate_key(account)
            generated_new_key = details is not None
        if details is None:
            continue

        key_id, fingerprint = details
        material = _export_material(key_id)
        if material is None:
            continue

        signing_changed = False
        if not account.signing_key or account.signing_key != key_id:
            account.signing_key = key_id
            config_updated = True
            signing_changed = True

        fields: List[OnePasswordField] = []
        if _needs_update(item, "public"):
            fields.append(
                OnePasswordField(
                    section="gpg",
                    label="public",
                    value=material.public_key + "\n",
                )
            )
        if _needs_update(item, "private"):
            fields.append(
                OnePasswordField(
                    section="gpg",
                    label="private",
                    value=material.private_key + "\n",
                    concealed=True,
                )
            )
        if _needs_update(item, "key_id") or (item and get_field_value(item, "gpg", "key_id") != key_id):
            fields.append(
                OnePasswordField(
                    section="gpg",
                    label="key_id",
                    value=key_id,
                )
            )
        if fingerprint and (
            _needs_update(item, "fingerprint")
            or (item and get_field_value(item, "gpg", "fingerprint") != fingerprint)
        ):
            fields.append(
                OnePasswordField(
                    section="gpg",
                    label="fingerprint",
                    value=fingerprint,
                )
            )

        fields_updated = False
        if fields:
            fields_updated = update_item_fields(account.op_vault, account.op_item, fields)
            if fields_updated:
                item = get_item(account.op_vault, account.op_item)

        if generated_new_key or fields_updated or signing_changed:
            updated_material.append((account, material))

    if config_updated:
        save_account_config(config)

    return updated_material
