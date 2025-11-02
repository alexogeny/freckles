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
from .meta import GIT_ACCOUNTS_DIR, HOME, REPOSITORY_LATEST
from .web import download_file


IDENTITY_BEGIN = "# >>> freckles global identity >>>"
IDENTITY_END = "# <<< freckles global identity <<<"
ACCOUNT_BEGIN = "# >>> freckles account includes >>>"
ACCOUNT_END = "# <<< freckles account includes <<<"


def download_git_files() -> None:
    for filename in [".gitconfig", ".gitignore"]:
        local_path = HOME / filename
        if local_path.exists():
            continue
        download_file(REPOSITORY_LATEST + f"git/{filename}", local_path)


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
        account_config = GIT_ACCOUNTS_DIR / f"{account.slug}.gitconfig"
        gitdir = account.directory.rstrip("/")
        lines.append(f'[includeIf "gitdir:{gitdir}/**/.git"]')
        lines.append(f"  path = {_home_relative(account_config)}")
    return lines


def _write_account_configs(config: AccountConfig) -> None:
    GIT_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    for account in config.accounts:
        config_path = GIT_ACCOUNTS_DIR / f"{account.slug}.gitconfig"
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
            f"  - {account.provider} ({account.scope}) -> {account.directory}"
        )
    print("\n".join(message))


def configure_git() -> AccountConfig:
    download_git_files()
    config = ensure_account_config()
    _write_account_configs(config)
    _update_gitconfig(config)
    _ensure_git_user_config(config)
    _summarise_accounts(config)
    return config


def get_account_config() -> AccountConfig:
    """Backwards compatible shim for account configuration access."""

    return _get_account_config(interactive=False)

