"""Helpers for provisioning shared SSH and GPG identity material."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .accounts import AccountConfig, save_account_config
from .debian import run
from .gpg import GpgMaterial, discover_secret_key, export_gpg_material, generate_secret_key
from .meta import CONFIG_DIR, HOME, SSH_DIR


IDENTITY_DIR = CONFIG_DIR / "identity"
PUBLIC_EXPORT_DIR = HOME / "Public" / "git-keys"
SHARED_SSH_KEY_PATH = SSH_DIR / "id_freckles_shared"
GPG_MARKER_PATH = IDENTITY_DIR / "gpg-key-id"


@dataclass
class SharedSshMaterial:
    """Details about the shared SSH key that was ensured on disk."""

    private_key_path: Path
    public_key_path: Path
    public_key: str
    fingerprint: str
    created: bool


@dataclass
class SharedGpgMaterial:
    """Information about the shared GPG key material."""

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


def ensure_shared_ssh_key(email: str) -> Optional[SharedSshMaterial]:
    """Ensure an SSH key exists for the supplied email address."""

    _ensure_directory(SSH_DIR)
    key_path = SHARED_SSH_KEY_PATH
    public_path = key_path.with_suffix(".pub")
    created = False

    if not key_path.exists() or not public_path.exists():
        command = " ".join(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-C",
                shlex.quote(email),
                "-f",
                shlex.quote(key_path.as_posix()),
                "-N",
                "''",
            ]
        )
        result = run(command)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "unknown error"
            print(f"Failed to generate shared SSH key: {message}")
            return None
        created = True

    _ensure_permissions(key_path, public_path)

    public_key = _read_text(public_path)
    if not public_key:
        return None

    fingerprint = _fingerprint_for_public_key(public_path)

    return SharedSshMaterial(
        private_key_path=key_path,
        public_key_path=public_path,
        public_key=public_key,
        fingerprint=fingerprint,
        created=created,
    )


def ensure_shared_gpg_material(config: AccountConfig) -> Optional[SharedGpgMaterial]:
    """Ensure a shared GPG key exists and update account configuration."""

    if not config.accounts:
        return None

    _ensure_directory(IDENTITY_DIR)
    default_account = config.get_default()
    marker_key = _read_text(GPG_MARKER_PATH)
    created = False
    lookup: Optional[tuple[str, str]] = None

    if marker_key:
        lookup = discover_secret_key(marker_key)
        if lookup is None:
            marker_key = ""

    if not lookup:
        lookup = discover_secret_key(default_account.email)

    if not lookup:
        lookup = generate_secret_key(default_account.display_name, default_account.email)
        created = lookup is not None

    if not lookup:
        print("Unable to locate or generate a shared GPG key for commit signing.")
        return None

    key_id, _fingerprint = lookup
    material = export_gpg_material(key_id)
    if material is None:
        print(f"Failed to export shared GPG key material for {key_id}.")
        return None

    if material.key_id and material.key_id != key_id:
        key_id = material.key_id

    if material.key_id:
        GPG_MARKER_PATH.write_text(material.key_id.strip() + "\n")

    config_updated = False
    for account in config.accounts:
        if account.signing_key != material.key_id:
            account.signing_key = material.key_id
            config_updated = True

    if config_updated:
        save_account_config(config)

    return SharedGpgMaterial(material=material, created=created)


def publish_public_material(
    ssh_material: Optional[SharedSshMaterial],
    gpg_material: Optional[SharedGpgMaterial],
) -> Dict[str, Path]:
    """Write exported material to a predictable directory for user access."""

    _ensure_directory(PUBLIC_EXPORT_DIR)
    outputs: Dict[str, Path] = {}

    if ssh_material:
        ssh_public = PUBLIC_EXPORT_DIR / "ssh.pub"
        ssh_public.write_text(ssh_material.public_key.strip() + "\n")
        outputs["ssh_public"] = ssh_public
        if ssh_material.fingerprint:
            ssh_fingerprint = PUBLIC_EXPORT_DIR / "ssh.fingerprint"
            ssh_fingerprint.write_text(ssh_material.fingerprint.strip() + "\n")
            outputs["ssh_fingerprint"] = ssh_fingerprint

    if gpg_material:
        gpg_public = PUBLIC_EXPORT_DIR / "gpg.asc"
        gpg_public.write_text(gpg_material.material.public_key.strip() + "\n")
        outputs["gpg_public"] = gpg_public
        key_id_path = PUBLIC_EXPORT_DIR / "gpg.key-id"
        key_id_path.write_text(gpg_material.material.key_id.strip() + "\n")
        outputs["gpg_key_id"] = key_id_path
        if gpg_material.material.fingerprint:
            gpg_fingerprint = PUBLIC_EXPORT_DIR / "gpg.fingerprint"
            gpg_fingerprint.write_text(
                gpg_material.material.fingerprint.strip() + "\n"
            )
            outputs["gpg_fingerprint"] = gpg_fingerprint

    return outputs

