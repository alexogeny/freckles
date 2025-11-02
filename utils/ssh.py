"""SSH configuration helpers leveraging 1Password for key management."""

from __future__ import annotations

import re
import shlex
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .accounts import GitAccount, get_account_config, save_account_config
from .debian import run
from .meta import HOME, KNOWN_HOSTS, SSH_CONFIG, SSH_DIR
from .one_password import (
    MultipleItemsFoundError,
    OnePasswordItem,
    ensure_op_connected,
    ensure_ssh_container,
    list_items,
    resolve_item_identifier,
)
from .shared_identity import ensure_shared_ssh_key, publish_public_material

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


def _prompt_for_item(account, catalog: List[OnePasswordItem]) -> Optional[OnePasswordItem]:
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
            return selected

        print("Please choose a valid option.")


def _auto_assign_items(
    accounts: List[GitAccount], catalog: List[OnePasswordItem]
) -> Dict[str, OnePasswordItem]:
    """Return automatic vault/item assignments keyed by account slug."""

    assignments: Dict[str, OnePasswordItem] = {}
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
            assignments[account.slug] = best
    return assignments


def _format_identity_path(path: Path) -> str:
    try:
        return f"~/{path.relative_to(HOME).as_posix()}"
    except ValueError:
        return path.as_posix()


def _render_host_block(account: GitAccount, identity_file: Path) -> str:
    identity = _format_identity_path(identity_file)
    block = textwrap.dedent(
        f"""
        Host {account.ssh_alias}
            HostName {account.provider}.com
            AddKeysToAgent yes
            IdentityFile {identity}
            User git
        """
    )
    return block


def _ensure_config_entry(
    account: GitAccount,
    existing_config: str,
    *,
    identity_file: Optional[Path] = None,
) -> Tuple[str, bool]:
    host_alias = account.ssh_alias
    identity_path = identity_file or (SSH_DIR / f"{account.slug}.{account.provider}")
    new_block = _render_host_block(account, identity_path)
    pattern = re.compile(
        rf"(^Host {re.escape(host_alias)}\n(?:[\t ].*\n?)*)",
        re.MULTILINE,
    )
    match = pattern.search(existing_config)
    if match:
        current_block = match.group(1)
        if not current_block.endswith("\n"):
            current_block += "\n"
        if current_block == new_block:
            return existing_config, False
        updated = existing_config[: match.start()] + new_block + existing_config[match.end() :]
        return updated, True

    updated_config = existing_config
    if updated_config and not updated_config.endswith("\n"):
        updated_config += "\n"
    updated_config += new_block
    return updated_config, True


def _install_keys_for_account(account) -> Tuple[bool, Optional[str]]:
    """Download and install SSH keys for a given account."""

    if not account.op_vault or not account.op_item:
        return False, None

    prepared = ensure_ssh_container(
        account.op_vault,
        account.op_item,
        create_if_missing=False,
    )
    if prepared is None:
        return False, (
            f"Unable to prepare 1Password item for {account.display_name} "
            f"({account.provider})."
        )

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
        public_text = public_key.read_text()
    except FileNotFoundError:
        public_text = ""
    try:
        private_text = key_path.read_text()
    except FileNotFoundError:
        private_text = ""

    if not public_text.strip() or "ssh-" not in public_text:
        for path in (key_path, public_key):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        return False, (
            f"The 1Password item {account.op_vault}/{account.op_item} does not contain "
            "an SSH public key. Please update the item manually and rerun the command."
        )

    if "PRIVATE KEY" not in private_text:
        for path in (key_path, public_key):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        return False, (
            f"The 1Password item {account.op_vault}/{account.op_item} does not contain "
            "an SSH private key. Please update the item manually and rerun the command."
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
    existing_config = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    has_one_password = any(
        account.op_vault and account.op_item for account in config.accounts
    )

    if not has_one_password:
        default_account = config.get_default()
        shared_material = ensure_shared_ssh_key(default_account.email)
        if shared_material is None:
            print("Skipping shared SSH setup because the key could not be generated.")
            return
        config_changed = False
        for account in config.accounts:
            existing_config, changed = _ensure_config_entry(
                account,
                existing_config,
                identity_file=shared_material.private_key_path,
            )
            config_changed = config_changed or changed
        if config_changed:
            if existing_config and not existing_config.endswith("\n"):
                existing_config += "\n"
            SSH_DIR.mkdir(parents=True, exist_ok=True)
            SSH_CONFIG.write_text(existing_config)
        add_result = run(
            f"ssh-add {shlex.quote(shared_material.private_key_path.as_posix())}"
        )
        if add_result.returncode != 0:
            message = add_result.stderr.strip() or add_result.stdout.strip() or "unknown error"
            print(f"Failed to add shared SSH key to ssh-agent: {message}")
        outputs = publish_public_material(shared_material, None)
        public_path = outputs.get("ssh_public")
        fingerprint_path = outputs.get("ssh_fingerprint")
        summary = [
            "\nShared SSH key configured locally.",
            f"  Host aliases: {', '.join(account.ssh_alias for account in config.accounts)}",
        ]
        if public_path:
            summary.append(f"  Public key: {public_path}")
        if fingerprint_path and shared_material.fingerprint:
            summary.append(f"  Fingerprint: {shared_material.fingerprint}")
            summary.append(f"  Fingerprint file: {fingerprint_path}")
        summary.append("Upload this public key to your Git hosting services.")
        print("\n".join(summary))
        return

    accounts_with_items = [
        account for account in config.accounts if account.op_vault and account.op_item
    ]
    needs_mapping = [
        account for account in config.accounts if not account.op_vault or not account.op_item
    ]

    catalog: List[OnePasswordItem] = []
    updated_config = False
    config_changed = False

    if accounts_with_items or needs_mapping:
        ensure_op_connected()

    if accounts_with_items:
        catalog = list_items()
        for account in list(accounts_with_items):
            try:
                resolved = resolve_item_identifier(
                    account.op_vault or "", account.op_item or "", catalog
                )
            except MultipleItemsFoundError as exc:
                reference = f"{account.op_vault}/{account.op_item}".strip("/")
                print(
                    "Multiple 1Password items match "
                    f"'{reference or account.display_name}' for {account.display_name}."
                )
                if interactive and exc.matches:
                    selection = _prompt_for_item(account, list(exc.matches))
                    if selection:
                        account.op_vault = selection.vault
                        account.op_item = selection.identifier
                        updated_config = True
                        continue
                account.op_item = None
                updated_config = True
                continue

            if resolved and resolved != account.op_item:
                account.op_item = resolved
                updated_config = True
            elif resolved is None:
                reference = f"{account.op_vault}/{account.op_item}".strip("/")
                print(
                    "Unable to find 1Password item "
                    f"'{reference or account.display_name}' for {account.display_name}."
                )
                if interactive and catalog:
                    selection = _prompt_for_item(account, catalog)
                    if selection:
                        account.op_vault = selection.vault
                        account.op_item = selection.identifier
                        updated_config = True
                        continue
                account.op_item = None
                updated_config = True

    accounts_with_items = [
        account for account in config.accounts if account.op_vault and account.op_item
    ]
    needs_mapping = [
        account for account in config.accounts if not account.op_vault or not account.op_item
    ]

    SSH_DIR.mkdir(parents=True, exist_ok=True)

    if needs_mapping:
        if not catalog:
            catalog = list_items()
        auto_assignments = _auto_assign_items(needs_mapping, catalog)
        for account in needs_mapping:
            if account.slug in auto_assignments:
                selection = auto_assignments[account.slug]
                account.op_vault = selection.vault
                account.op_item = selection.identifier
                updated_config = True
                print(
                    f"Automatically mapped {account.display_name} ({account.provider})"
                    f" -> {selection.vault}/{selection.title}"
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
                account.op_vault = selection.vault
                account.op_item = selection.identifier
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
            existing_config, changed = _ensure_config_entry(account, existing_config)
            config_changed = config_changed or changed
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
            account.op_vault = selection.vault
            account.op_item = selection.identifier
            updated_config = True
            success, error = _install_keys_for_account(account)
            if success:
                existing_config, changed = _ensure_config_entry(account, existing_config)
                config_changed = config_changed or changed
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
    if config_changed:
        if existing_config and not existing_config.endswith("\n"):
            existing_config += "\n"
        SSH_CONFIG.write_text(existing_config)


