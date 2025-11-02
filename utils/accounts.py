"""Account configuration helpers for onboarding git and ssh tooling."""

from __future__ import annotations

import json
from json import JSONDecodeError
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .meta import (
    CONFIG_DIR,
    HOME,
    GIT_ACCOUNT_CONFIG_PATH,
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "account"


def _normalise_directory(path: str) -> str:
    expanded = Path(path).expanduser()
    try:
        relative = expanded.relative_to(HOME)
    except ValueError:
        return expanded.as_posix()
    return f"~/{relative.as_posix()}"


@dataclass
class GitAccount:
    """Stores metadata about an individual git identity."""

    scope: str
    provider: str
    display_name: str
    email: str
    directory: str
    username: Optional[str] = None
    signing_key: Optional[str] = None
    op_vault: Optional[str] = None
    op_item: Optional[str] = None
    ssh_host: Optional[str] = None

    def __post_init__(self) -> None:
        self.scope = self.scope.strip()
        self.provider = self.provider.strip().lower()
        self.display_name = self.display_name.strip()
        self.email = self.email.strip()
        self.directory = _normalise_directory(self.directory.strip())
        if self.username:
            self.username = self.username.strip()
        if self.signing_key:
            self.signing_key = self.signing_key.strip()
        if self.op_vault:
            self.op_vault = self.op_vault.strip()
        if self.op_item:
            self.op_item = self.op_item.strip()
        if self.ssh_host:
            self.ssh_host = self.ssh_host.strip()

    @property
    def slug(self) -> str:
        return _slugify(f"{self.scope}-{self.provider}")

    @property
    def ssh_alias(self) -> str:
        alias = self.ssh_host
        if alias:
            return alias
        return f"{self.provider}.com-{self.slug}"

    def as_serialisable(self) -> dict:
        data = asdict(self)
        return {key: value for key, value in data.items() if value}


@dataclass
class AccountConfig:
    accounts: List[GitAccount]
    default_account: str

    def get_default(self) -> GitAccount:
        for account in self.accounts:
            if account.slug == self.default_account:
                return account
        raise ValueError("Default account not present in configuration")


def _default_accounts() -> AccountConfig:
    accounts = [
        GitAccount(
            scope="private",
            provider="github",
            display_name="alexogeny",
            email="6896115+alexogeny@users.noreply.github.com",
            directory="~/private/github",
            username="alexogeny",
        ),
        GitAccount(
            scope="private",
            provider="gitlab",
            display_name="alexogeny",
            email="8857503-alexogeny@users.noreply.gitlab.com",
            directory="~/private/gitlab",
            username="alexogeny",
        ),
    ]
    return AccountConfig(accounts=accounts, default_account=accounts[0].slug)


def load_account_config() -> Optional[AccountConfig]:
    if not GIT_ACCOUNT_CONFIG_PATH.exists():
        return None
    data = json.loads(GIT_ACCOUNT_CONFIG_PATH.read_text())
    accounts = [GitAccount(**account) for account in data.get("accounts", [])]
    default_account = data.get("default_account") or (accounts[0].slug if accounts else "")
    return AccountConfig(accounts=accounts, default_account=default_account)


def get_account_config(*, interactive: bool = False) -> AccountConfig:
    """Return a valid git account configuration.

    The configuration is loaded from disk when available. If the persisted
    configuration is missing or invalid a new configuration is generated.

    Parameters
    ----------
    interactive:
        Whether to allow interactive prompts when a configuration needs to be
        generated. Defaults to ``False`` so non-interactive environments can
        fall back to sensible defaults automatically.
    """

    try:
        config = load_account_config()
    except (OSError, JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Failed to load git account configuration: {exc}. Regenerating configuration.")
        config = None

    if config is None or not config.accounts:
        return ensure_account_config(interactive=interactive)

    if not any(account.slug == config.default_account for account in config.accounts):
        config.default_account = config.accounts[0].slug

    return config


def save_account_config(config: AccountConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "accounts": [account.as_serialisable() for account in config.accounts],
        "default_account": config.default_account,
    }
    GIT_ACCOUNT_CONFIG_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _prompt(prompt: str, default: Optional[str] = None, allow_empty: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            response = input(f"{prompt}{suffix}: ").strip()
        except EOFError:
            return default or ""
        if not response and default is not None:
            response = default
        if response:
            return response
        if allow_empty:
            return ""
        print("Value is required. Please try again.")


def _prompt_choice(prompt: str, choices: Iterable[str], default: Optional[str] = None) -> str:
    normalised_choices = [choice.lower() for choice in choices]
    default_value = default.lower() if default else None
    options = ", ".join(normalised_choices)
    while True:
        answer = _prompt(f"{prompt} ({options})", default=default_value)
        if answer.lower() in normalised_choices:
            return answer.lower()
        print(f"Please choose one of: {options}.")


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
    default_str = "y" if default else "n"
    while True:
        answer = _prompt(f"{prompt} [y/n]", default=default_str)
        if answer.lower() in {"y", "yes"}:
            return True
        if answer.lower() in {"n", "no"}:
            return False
        print("Please answer 'y' or 'n'.")


def _prompt_account(existing: Optional[GitAccount] = None) -> GitAccount:
    scope_default = existing.scope if existing else "personal"
    scope = _prompt("Account scope (e.g. personal or work/company)", default=scope_default)

    provider_default = existing.provider if existing else "github"
    provider = _prompt_choice("Git provider", ["github", "gitlab"], default=provider_default)

    display_default = existing.display_name if existing else scope.title()
    display_name = _prompt("Commit author name", default=display_default)

    username_default = existing.username if existing and existing.username else ""
    username = _prompt("Account username", default=username_default, allow_empty=True)

    email_default = existing.email if existing else ""
    email = _prompt("Commit email", default=email_default)

    if existing:
        directory_default = existing.directory
    else:
        slug_parts = scope.replace(" ", "-").replace("/", "/")
        if "/" in slug_parts:
            base_dir = f"~/{slug_parts}"
        elif scope.lower() in {"personal", "private"}:
            base_dir = "~/private"
        elif scope.lower().startswith("work"):
            base_dir = "~/work"
        else:
            base_dir = f"~/{_slugify(scope)}"
        directory_default = f"{base_dir}/{provider}"
    directory = _prompt("Directory prefix for repositories", default=directory_default)

    signing_key_default = existing.signing_key if existing and existing.signing_key else ""
    signing_key = _prompt("GPG signing key (leave blank if none)", default=signing_key_default, allow_empty=True)

    if existing and existing.op_vault and existing.op_item:
        ssh_default = f"{existing.op_vault}/{existing.op_item}"
    else:
        ssh_default = ""
    ssh_path = _prompt(
        "1Password vault/item for SSH key (leave blank to skip)",
        default=ssh_default,
        allow_empty=True,
    )
    op_vault: Optional[str] = None
    op_item: Optional[str] = None
    if ssh_path:
        if "/" not in ssh_path:
            print("Expected format '<vault>/<item>'. Ignoring value.")
        else:
            op_vault, op_item = ssh_path.split("/", 1)

    ssh_host_default = existing.ssh_host if existing and existing.ssh_host else ""
    ssh_host = _prompt(
        "Custom SSH host alias (leave blank to auto-generate)",
        default=ssh_host_default,
        allow_empty=True,
    )

    return GitAccount(
        scope=scope,
        provider=provider,
        display_name=display_name,
        email=email,
        directory=directory,
        username=username or None,
        signing_key=signing_key or None,
        op_vault=op_vault,
        op_item=op_item,
        ssh_host=ssh_host or None,
    )


def _prompt_default_account(accounts: List[GitAccount], default_slug: str) -> str:
    if len(accounts) == 1:
        return accounts[0].slug
    print("\nSelect the default git identity:")
    for index, account in enumerate(accounts, start=1):
        marker = "*" if account.slug == default_slug else " "
        print(
            f"  {index}. [{marker}] {account.display_name} <{account.email}> "
            f"({account.provider} @ {account.scope})"
        )
    while True:
        choice = _prompt("Enter the number for the default identity", default="1")
        if choice.isdigit():
            position = int(choice)
            if 1 <= position <= len(accounts):
                return accounts[position - 1].slug
        print("Please enter a valid option number.")


def prompt_for_account_config(existing: Optional[AccountConfig] = None) -> AccountConfig:
    accounts: List[GitAccount] = []
    if existing:
        for account in existing.accounts:
            print(f"\nReviewing configuration for {account.provider} ({account.scope})")
            accounts.append(_prompt_account(existing=account))
        add_more = _prompt_yes_no("Would you like to add another git account?", default=False)
    else:
        add_more = True

    while add_more:
        print("\nConfigure a git identity")
        accounts.append(_prompt_account())
        add_more = _prompt_yes_no("Add another account?", default=False)

    if not accounts:
        raise RuntimeError("At least one git account must be configured.")

    seen = set()
    for account in accounts:
        if account.slug in seen:
            raise RuntimeError(
                "Duplicate account scopes detected. Please choose unique scopes for each provider."
            )
        seen.add(account.slug)

    default_slug = existing.default_account if existing else accounts[0].slug
    default_account = _prompt_default_account(accounts, default_slug)

    return AccountConfig(accounts=accounts, default_account=default_account)


def ensure_account_config(interactive: bool = True) -> AccountConfig:
    config = load_account_config()
    if config:
        if interactive and sys.stdin.isatty():
            if _prompt_yes_no("Existing git account configuration found. Review it?", default=False):
                config = prompt_for_account_config(config)
                save_account_config(config)
        return config

    if not interactive or not sys.stdin.isatty():
        config = _default_accounts()
        save_account_config(config)
        return config

    config = prompt_for_account_config()
    save_account_config(config)
    return config

