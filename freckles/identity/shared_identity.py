"""Helpers for provisioning per-account SSH and GPG identity material."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from freckles.system.debian import run
from utils.meta import CONFIG_DIR, HOME, SSH_DIR
from .accounts import AccountConfig, GitAccount, save_account_config
from .gpg import GpgMaterial, discover_secret_key, export_gpg_material, generate_secret_key


IDENTITY_DIR = CONFIG_DIR / "identity"
PUBLIC_EXPORT_DIR = HOME / "Public" / "git-keys"


@dataclass
class AccountSshMaterial:
    """Details about an SSH key that was ensured for a git account."""

    account_slug: str
    private_key_path: Path
    public_key_path: Path
    public_key: str
    fingerprint: str
    created: bool


@dataclass
class AccountGpgMaterial:
    """Information about GPG key material for a git account."""

    account_slug: str
    material: GpgMaterial
    created: bool


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _read_text(path: Path) -> str:
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        return ""


def _ensure_permissions(private_path: Path, public_path: Path) -> None:
    try:
        private_path.chmod(0o600)
    except FileNotFoundError:
        pass
    try:
        public_path.chmod(0o644)
    except FileNotFoundError:
        pass


def _fingerprint_for_public_key(public_path: Path) -> str:
    command = f"ssh-keygen -lf {shlex.quote(public_path.as_posix())}"
    result = run(command)
    if result.returncode != 0:
        return ""
    stdout = (result.stdout or "").strip().splitlines()
    if not stdout:
        return ""
    parts = stdout[0].split()
    if len(parts) >= 2:
        return parts[1]
    return stdout[0]


def _slugify_token(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "id"


def _ssh_key_paths(account: GitAccount) -> Tuple[Path, Path]:
    host_token = _slugify_token(account.ssh_host or account.provider)
    basename = f"{account.alias_slug}.{host_token}.id_ed25519"
    key_path = SSH_DIR / basename
    return key_path, key_path.with_suffix(".pub")


def _gpg_marker_path(account: GitAccount) -> Path:
    return IDENTITY_DIR / f"{account.slug}.gpg-key-id"


def ensure_account_ssh_key(account: GitAccount) -> Optional[AccountSshMaterial]:
    """Ensure an SSH key exists for the supplied git account."""

    _ensure_directory(SSH_DIR)
    key_path, public_path = _ssh_key_paths(account)
    created = False

    if not key_path.exists() or not public_path.exists():
        command = " ".join(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-C",
                shlex.quote(account.email),
                "-f",
                shlex.quote(key_path.as_posix()),
                "-N",
                "''",
            ]
        )
        result = run(command)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "unknown error"
            print(f"Failed to generate SSH key for {account.slug}: {message}")
            return None
        created = True

    _ensure_permissions(key_path, public_path)

    public_key = _read_text(public_path)
    if not public_key:
        print(f"Unable to read public SSH key for {account.slug} at {public_path}")
        return None

    fingerprint = _fingerprint_for_public_key(public_path)

    return AccountSshMaterial(
        account_slug=account.slug,
        private_key_path=key_path,
        public_key_path=public_path,
        public_key=public_key,
        fingerprint=fingerprint,
        created=created,
    )


def ensure_ssh_materials(config: AccountConfig) -> Dict[str, AccountSshMaterial]:
    """Ensure SSH keys exist for all configured accounts."""

    materials: Dict[str, AccountSshMaterial] = {}
    for account in config.accounts:
        material = ensure_account_ssh_key(account)
        if material is None:
            print(f"Skipping SSH configuration for {account.slug} due to prior errors.")
            continue
        materials[account.slug] = material
    return materials


def ensure_account_gpg_material(account: GitAccount) -> Optional[AccountGpgMaterial]:
    """Ensure a GPG key exists for the supplied git account."""

    _ensure_directory(IDENTITY_DIR)
    marker_path = _gpg_marker_path(account)
    marker_key = _read_text(marker_path)
    created = False
    lookup: Optional[tuple[str, str]] = None

    if account.signing_key:
        lookup = discover_secret_key(account.signing_key)

    if not lookup and marker_key:
        lookup = discover_secret_key(marker_key)
        if lookup is None:
            marker_key = ""

    if not lookup:
        lookup = discover_secret_key(account.email)

    if not lookup:
        lookup = generate_secret_key(account.display_name, account.email)
        created = lookup is not None

    if not lookup:
        print(f"Unable to locate or generate a GPG key for {account.slug}.")
        return None

    key_id, _fingerprint = lookup
    material = export_gpg_material(key_id)
    if material is None:
        print(f"Failed to export GPG key material for {key_id}.")
        return None

    if material.key_id and material.key_id != key_id:
        key_id = material.key_id

    if key_id:
        marker_path.write_text(key_id.strip() + "\n")

    return AccountGpgMaterial(
        account_slug=account.slug,
        material=material,
        created=created,
    )


def ensure_gpg_materials(config: AccountConfig) -> Tuple[Dict[str, AccountGpgMaterial], bool]:
    """Ensure GPG keys exist for all configured accounts and update signing keys."""

    materials: Dict[str, AccountGpgMaterial] = {}
    config_updated = False

    for account in config.accounts:
        material = ensure_account_gpg_material(account)
        if material is None:
            print(f"Skipping GPG configuration for {account.slug} due to prior errors.")
            continue
        materials[account.slug] = material
        key_id = material.material.key_id
        if key_id and account.signing_key != key_id:
            account.signing_key = key_id
            config_updated = True

    if config_updated:
        save_account_config(config)

    return materials, config_updated


def publish_public_materials(
    ssh_materials: Dict[str, AccountSshMaterial],
    gpg_materials: Dict[str, AccountGpgMaterial],
) -> Dict[str, Dict[str, Path]]:
    """Write exported material to a predictable directory for user access."""

    _ensure_directory(PUBLIC_EXPORT_DIR)
    outputs: Dict[str, Dict[str, Path]] = {}

    for slug, ssh_material in ssh_materials.items():
        slug_outputs = outputs.setdefault(slug, {})
        ssh_public = PUBLIC_EXPORT_DIR / f"{slug}.ssh.pub"
        ssh_public.write_text(ssh_material.public_key.strip() + "\n")
        slug_outputs["ssh_public"] = ssh_public
        if ssh_material.fingerprint:
            ssh_fingerprint = PUBLIC_EXPORT_DIR / f"{slug}.ssh.fingerprint"
            ssh_fingerprint.write_text(ssh_material.fingerprint.strip() + "\n")
            slug_outputs["ssh_fingerprint"] = ssh_fingerprint

    for slug, gpg_material in gpg_materials.items():
        slug_outputs = outputs.setdefault(slug, {})
        gpg_public = PUBLIC_EXPORT_DIR / f"{slug}.gpg.asc"
        gpg_public.write_text(gpg_material.material.public_key.strip() + "\n")
        slug_outputs["gpg_public"] = gpg_public
        key_id_path = PUBLIC_EXPORT_DIR / f"{slug}.gpg.key-id"
        key_id_path.write_text(gpg_material.material.key_id.strip() + "\n")
        slug_outputs["gpg_key_id"] = key_id_path
        if gpg_material.material.fingerprint:
            gpg_fingerprint = PUBLIC_EXPORT_DIR / f"{slug}.gpg.fingerprint"
            gpg_fingerprint.write_text(gpg_material.material.fingerprint.strip() + "\n")
            slug_outputs["gpg_fingerprint"] = gpg_fingerprint

    return outputs
