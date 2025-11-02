"""SSH configuration helpers leveraging 1Password for key management."""

from __future__ import annotations

import sys
import textwrap
from typing import Dict, List, Optional, Tuple

from .accounts import GitAccount, get_account_config, save_account_config
from .debian import run
from .meta import KNOWN_HOSTS, SSH_CONFIG, SSH_DIR
from .one_password import OnePasswordItem, ensure_op_connected, list_items

known_hosts_content = textwrap.dedent("""
gitlab.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAfuCHKVTjquxvt6CM6tdG4SLp1Btn/nOeHHE5UOzRdf
gitlab.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsj2bNKTBSpIYDEGk9KxsGh3mySTRgMtXL583qmBpzeQ+jqCMRgBqB98u3z++J1sKlXHWfM9dyhSevkMwSbhoR8XIq/U0tCNyokEi/ueaBMCvbcTHhO7FcwzY92WK4Yt0aGROY5qX2UKSeOvuP4D6TPqKF1onrSzH9bx9XUf2lEdWT/ia1NEKjunUqu1xOB/StKDHMoX4/OKyIzuS0q/T1zOATthvasJFoPrAjkohTyaDUz2LN5JoH839hViyEG82yB+MjcFV5MU3N1l1QL3cVUCh93xSaua1N85qivl+siMkPGbO5xR/En4iEY6K2XPASUEMaieWVNTRCtJ4S8H+9
gitlab.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBFSMqzJeV9rUzU4kWitGjeR4PWSa29SPqJ1fVkhtj3Hw9xjLVXVYrU9QlYWrOLXBpQ6KWjbjTDTdDkoohFzgbEY=

github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=
github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=
""")
def write_known_hosts() -> None:
    if not KNOWN_HOSTS.exists():
        KNOWN_HOSTS.write_text(known_hosts_content)


def _score_item(account: GitAccount, item: OnePasswordItem) -> int:
    """Return a simple relevance score between an account and 1Password item."""

    text = f"{item.title} {item.vault}".lower()
    score = 0
    provider = account.provider.lower()
    scope = account.scope.lower()
    alias = (account.alias or "").lower()
    display = account.display_name.lower()

    if provider and provider in text:
        score += 3
    if scope and scope in text:
        score += 2
    if alias and alias in text:
        score += 3
    if display and display in text:
        score += 1
    alias_tokens = [token for token in alias.replace("/", " ").replace("-", " ").split() if token]
    for token in alias_tokens:
        if token and token in text:
            score += 1
    if account.username and account.username.lower() in text:
        score += 2
    if "ssh" in item.title.lower():
        score += 1
    if item.favorite:
        score += 1
    return score


def _prompt_for_item(account, catalog: List[OnePasswordItem]) -> Optional[Tuple[str, str]]:
    """Prompt the user to associate a 1Password item with an account."""

    if not catalog:
        print("No 1Password items available to assign SSH keys.")
        return None

    sorted_items = sorted(
        catalog,
        key=lambda item: (_score_item(account, item), item.title.lower()),
        reverse=True,
    )

    header = (
        f"\nNo SSH key mapping found for {account.display_name} "
        f"({account.provider}, {account.scope})."
    )
    print(header)

    choices = [item for item in sorted_items if _score_item(account, item) > 0][:5]
    if not choices:
        choices = sorted_items

    while True:
        print("Select the 1Password item that stores the SSH key:")
        option_map: Dict[str, OnePasswordItem] = {}
        for index, item in enumerate(choices, start=1):
            option_map[str(index)] = item
            print(f"  {index}. {item.label()}")
        print("  0. Skip this account")
        if choices is not sorted_items:
            print("  m. Show more items")

        try:
            answer = input("Choice: ").strip().lower()
        except EOFError:
            return None

        if answer in {"", "0"}:
            return None
        if answer == "m" and choices is not sorted_items:
            choices = sorted_items
            continue
        if answer in option_map:
            selected = option_map[answer]
            return selected.vault, selected.title

        print("Please choose a valid option.")


def _auto_assign_items(
    accounts: List[GitAccount], catalog: List[OnePasswordItem]
) -> Dict[str, Tuple[str, str]]:
    """Return automatic vault/item assignments keyed by account slug."""

    assignments: Dict[str, Tuple[str, str]] = {}
    for account in accounts:
        ranked = sorted(
            catalog,
            key=lambda item: (_score_item(account, item), item.title.lower()),
            reverse=True,
        )
        if not ranked:
            continue
        best = ranked[0]
        best_score = _score_item(account, best)
        if best_score <= 0:
            continue
        second_score = _score_item(account, ranked[1]) if len(ranked) > 1 else None
        unique_high = second_score is None or best_score >= (second_score + 2)
        if best_score >= 5 or unique_high:
            assignments[account.slug] = (best.vault, best.title)
    return assignments


def _ensure_config_entry(account, existing_config: str) -> str:
    host_alias = account.ssh_alias
    if f"Host {host_alias}" in existing_config:
        return existing_config

    key_path = SSH_DIR / f"{account.slug}.{account.provider}"
    config_entry = textwrap.dedent(
        f"""
        Host {host_alias}
            HostName {account.provider}.com
            AddKeysToAgent yes
            IdentityFile ~/.ssh/{key_path.name}
            User git
    """
    )
    with SSH_CONFIG.open("a") as fh:
        fh.write(config_entry)
    return existing_config + config_entry


def _install_keys_for_account(account) -> Tuple[bool, Optional[str]]:
    """Download and install SSH keys for a given account."""

    if not account.op_vault or not account.op_item:
        return False, None

    key_path = SSH_DIR / f"{account.slug}.{account.provider}"
    public_key = key_path.with_suffix(".pub")
    op_prefix = f"op://{account.op_vault}/{account.op_item}/ssh"

    public_result = run(
        f'op read --force --out-file "{public_key}" "{op_prefix}/public"'
    )
    if public_result.returncode != 0:
        message = public_result.stderr.strip() or public_result.stdout.strip() or "unknown error"
        return False, (
            f"Failed to retrieve public key for {account.display_name} "
            f"from {account.op_vault}/{account.op_item}: {message}"
        )

    private_result = run(
        f'op read --force --out-file "{key_path}" "{op_prefix}/private"'
    )
    if private_result.returncode != 0:
        message = private_result.stderr.strip() or private_result.stdout.strip() or "unknown error"
        return False, (
            f"Failed to retrieve private key for {account.display_name} "
            f"from {account.op_vault}/{account.op_item}: {message}"
        )

    try:
        private_key_path = key_path
        private_key_path.chmod(0o600)
        public_key.chmod(0o644)
    except FileNotFoundError:
        pass

    add_result = run(f'ssh-add "{key_path}"')
    if add_result.returncode != 0:
        message = add_result.stderr.strip() or add_result.stdout.strip() or "unknown error"
        return False, f"Failed to add {key_path} to ssh-agent: {message}"

    return True, None


def configure_ssh():
    write_known_hosts()
    interactive = sys.stdin.isatty()
    config = get_account_config(interactive=interactive)
    ensure_op_connected()
    existing_config = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    SSH_DIR.mkdir(parents=True, exist_ok=True)

    catalog: List[OnePasswordItem] = []
    needs_mapping = [
        account for account in config.accounts if not account.op_vault or not account.op_item
    ]

    updated_config = False
    if needs_mapping:
        catalog = list_items()
        auto_assignments = _auto_assign_items(needs_mapping, catalog)
        for account in needs_mapping:
            if account.slug in auto_assignments:
                vault, item = auto_assignments[account.slug]
                account.op_vault, account.op_item = vault, item
                updated_config = True
                print(
                    f"Automatically mapped {account.display_name} ({account.provider})"
                    f" -> {vault}/{item}"
                )
        needs_mapping = [
            account
            for account in needs_mapping
            if not account.op_vault or not account.op_item
        ]

    if needs_mapping and interactive:
        for account in needs_mapping:
            selection = _prompt_for_item(account, catalog)
            if selection:
                account.op_vault, account.op_item = selection
                updated_config = True
    elif needs_mapping:
        print(
            "Skipping SSH key assignment for accounts without 1Password metadata "
            "in non-interactive mode."
        )

    if updated_config:
        save_account_config(config)

    failures: Dict[str, str] = {}
    for account in config.accounts:
        if not account.op_vault or not account.op_item:
            continue
        success, error = _install_keys_for_account(account)
        if success:
            existing_config = _ensure_config_entry(account, existing_config)
        elif error:
            failures[account.slug] = error
            print(error)

    if failures and interactive:
        if not catalog:
            catalog = list_items()
        for account in config.accounts:
            if account.slug not in failures:
                continue
            print("\n" + failures[account.slug])
            selection = _prompt_for_item(account, catalog)
            if not selection:
                continue
            account.op_vault, account.op_item = selection
            updated_config = True
            success, error = _install_keys_for_account(account)
            if success:
                existing_config = _ensure_config_entry(account, existing_config)
                failures.pop(account.slug, None)
            elif error:
                failures[account.slug] = error
                print(error)

    if updated_config:
        save_account_config(config)

    if failures:
        print("\nSome SSH keys could not be installed:")
        for message in failures.values():
            print(f"  - {message}")
