"""Identity domain helpers (accounts, SSH, GPG)."""

from .accounts import AccountConfig, GitAccount, get_account_config, ensure_account_config, save_account_config
from .gpg import GpgMaterial, discover_secret_key, export_gpg_material, generate_secret_key
from .shared_identity import (
    AccountGpgMaterial,
    AccountSshMaterial,
    ensure_account_gpg_material,
    ensure_account_ssh_key,
    ensure_gpg_materials,
    ensure_ssh_materials,
    publish_public_materials,
)

__all__ = [
    "AccountConfig",
    "GitAccount",
    "get_account_config",
    "ensure_account_config",
    "save_account_config",
    "GpgMaterial",
    "discover_secret_key",
    "export_gpg_material",
    "generate_secret_key",
    "AccountGpgMaterial",
    "AccountSshMaterial",
    "ensure_account_gpg_material",
    "ensure_account_ssh_key",
    "ensure_gpg_materials",
    "ensure_ssh_materials",
    "publish_public_materials",
]
