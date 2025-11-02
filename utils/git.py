"""Git onboarding helpers for dotfile configuration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from .accounts import (
    AccountConfig,
    GitAccount,
    ensure_account_config,
    get_account_config as _get_account_config,
)
from .meta import HOME
from .shared_identity import ensure_shared_gpg_material, publish_public_material


IDENTITY_BEGIN = "# >>> freckles global identity >>>"
IDENTITY_END = "# <<< freckles global identity <<<"
ACCOUNT_BEGIN = "# >>> freckles account includes >>>"
ACCOUNT_END = "# <<< freckles account includes <<<"


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "git"


def _template_file(filename: str) -> Path:
    path = TEMPLATE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing template git file: {filename}")
    return path


def download_git_files() -> None:
    for filename in [".gitconfig", ".gitignore"]:
        template = _template_file(filename)
        local_path = HOME / filename
        if local_path.exists():
            content = local_path.read_text()
            if all(marker in content for marker in (IDENTITY_BEGIN, IDENTITY_END, ACCOUNT_BEGIN, ACCOUNT_END)):
                continue
        local_path.write_text(template.read_text())


def _home_relative(path: Path) -> str:
    try:
        return f"~/{path.relative_to(HOME).as_posix()}"
    except ValueError:
        return path.as_posix()


def _replace_block(text: str, begin: str, end: str, replacement_lines: Iterable[str]) -> str:
    if begin not in text or end not in text:
        raise RuntimeError("Missing managed block markers in .gitconfig")
    before, remainder = text.split(begin, 1)
    block, after = remainder.split(end, 1)
    replacement = "\n".join(line.rstrip() for line in replacement_lines if line is not None)
    replacement = replacement.strip("\n")
    if replacement:
        block_text = f"{begin}\n{replacement}\n{end}"
    else:
        block_text = f"{begin}\n{end}"
    return before + block_text + after


def _identity_lines(account: GitAccount) -> list[str]:
    lines = [
        "[user]",
        f"  name = {account.display_name}",
        f"  email = {account.email}",
    ]
    if account.signing_key:
        lines.append(f"  signingkey = {account.signing_key}")
    return lines


def _account_include_lines(config: AccountConfig) -> list[str]:
    lines: list[str] = []
    for account in config.accounts:
        account_config = HOME / f".{account.slug}.gitconfig"
        gitdir = account.directory.rstrip("/")
        lines.append(f'[includeIf "gitdir:{gitdir}/**/.git"]')
        lines.append(f"  path = {_home_relative(account_config)}")
    return lines


def _write_account_configs(config: AccountConfig) -> None:
    for account in config.accounts:
        config_path = HOME / f".{account.slug}.gitconfig"
        sections = [
            "[user]",
            f"  name = {account.display_name}",
            f"  email = {account.email}",
        ]
        if account.signing_key:
            sections.append(f"  signingkey = {account.signing_key}")
        if account.username and account.provider == "github":
            sections.append("")
            sections.append("[github]")
            sections.append(f"  user = {account.username}")
        config_path.write_text("\n".join(sections).rstrip() + "\n")


def _update_gitconfig(config: AccountConfig) -> None:
    gitconfig_path = HOME / ".gitconfig"
    if not gitconfig_path.exists():
        raise RuntimeError("Expected ~/.gitconfig to exist before configuring git")
    text = gitconfig_path.read_text()
    default_account = config.get_default()
    text = _replace_block(text, IDENTITY_BEGIN, IDENTITY_END, _identity_lines(default_account))
    text = _replace_block(text, ACCOUNT_BEGIN, ACCOUNT_END, _account_include_lines(config))
    gitconfig_path.write_text(text)


def _ensure_git_user_config(config: AccountConfig) -> None:
    default_account = config.get_default()
    subprocess.run(
        ["git", "config", "--global", "user.name", default_account.display_name],
        check=False,
    )
    subprocess.run(
        ["git", "config", "--global", "user.email", default_account.email],
        check=False,
    )
    if default_account.signing_key:
        subprocess.run(
            ["git", "config", "--global", "user.signingkey", default_account.signing_key],
            check=False,
        )


def _summarise_accounts(config: AccountConfig) -> None:
    message = [
        "Configured git identities:",
        f"  default: {config.get_default().display_name} <{config.get_default().email}>",
    ]
    for account in config.accounts:
        message.append(
            f"  - {account.alias_slug}: {account.provider} ({account.scope}) -> {account.directory}"
        )
    print("\n".join(message))


def configure_git() -> AccountConfig:
    download_git_files()
    config = ensure_account_config()
    shared_gpg = ensure_shared_gpg_material(config)
    _write_account_configs(config)
    _update_gitconfig(config)
    _ensure_git_user_config(config)
    _summarise_accounts(config)
    if shared_gpg:
        outputs = publish_public_material(None, shared_gpg)
        public_path = outputs.get("gpg_public")
        fingerprint_path = outputs.get("gpg_fingerprint")
        key_id_path = outputs.get("gpg_key_id")
        message = [
            "\nShared GPG signing key configured locally.",
            f"  Key ID: {shared_gpg.material.key_id}",
        ]
        if shared_gpg.material.fingerprint:
            message.append(f"  Fingerprint: {shared_gpg.material.fingerprint}")
        if public_path:
            message.append(f"  Public key: {public_path}")
        if fingerprint_path:
            message.append(f"  Fingerprint file: {fingerprint_path}")
        if key_id_path:
            message.append(f"  Key id file: {key_id_path}")
        message.append(
            "Upload this public key to your Git hosting services to enable commit signing."
        )
        print("\n".join(message))
    return config


def get_account_config() -> AccountConfig:
    """Backwards compatible shim for account configuration access."""

    return _get_account_config(interactive=False)

