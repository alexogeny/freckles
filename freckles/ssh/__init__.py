"""SSH configuration helpers for per-account key management."""

from __future__ import annotations

import re
import shlex
import sys
import textwrap
from pathlib import Path
from typing import Dict, Optional, Tuple

from freckles.identity.accounts import GitAccount, get_account_config
from freckles.system.debian import run
from freckles.core.meta import HOME, KNOWN_HOSTS, SSH_CONFIG, SSH_DIR
from freckles.identity.shared_identity import (
    AccountSshMaterial,
    ensure_ssh_materials,
    publish_public_materials,
)

known_hosts_content = textwrap.dedent("""
gitlab.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAfuCHKVTjquxvt6CM6tdG4SLp1Btn/nOeHHE5UOzRdf
gitlab.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsj2bNKTBSpIYDEGk9KxsGh3mySTRgMtXL583qmBpzeQ+jqCMRgBqB98u3z++J1sKlXHWfM9dyhSevkMwSbhoR8XIq/U0tCNyokEi/ueaBMCvbcTHhO7FcwzY92WK4Yt0aGROY5qX2UKSeOvuP4D6TPqKF1onrSzH9bx9XUf2lEdWT/ia1NEKjunUqu1xOB/StKDHMoX4/OKyIzuS0q/T1zOATthvasJFoPrAjkohTyaDUz2LN5JoH839hViyEG82yB+MjcFV5MU3N1l1QL3cVUCh93xSaua1N85qivl+siMkPGbO5xR/En4iEY6K2XPASUEMaieWVNTRCtJ4S8H+9
gitlab.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBFSMqzJeV9rUzU4kWitGjeR4PWSa29SPqJ1fVkhtj3Hw9xjLVXVYrU9QlYWrOLXBpQ6KWjbjTDTdDkoohFzgbEY=

github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=
github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=
""")


def write_known_hosts() -> None:
    """Ensure GitHub/GitLab host keys exist locally to avoid interactive prompts."""
    if KNOWN_HOSTS.exists():
        return
    KNOWN_HOSTS.write_text(known_hosts_content)


IDENTITY_PATTERN = re.compile(r"^(\s*)IdentityFile\s+(.+)$", re.IGNORECASE)


def _format_identity_path(path: Path) -> str:
    """Render a human-friendly identity path relative to ``HOME`` when possible."""
    try:
        return f"~/{path.relative_to(HOME).as_posix()}"
    except ValueError:
        return path.as_posix()


def _render_host_block(account: GitAccount, identity_file: Path) -> str:
    """Return a canonical ``Host`` block for the provided account."""
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


def _host_pattern(alias: str) -> re.Pattern[str]:
    return re.compile(rf"(^Host {re.escape(alias)}\n(?:[\t ].*\n?)*)", re.MULTILINE)


def _canonical_identity_line(path: Path) -> str:
    return f"    IdentityFile {_format_identity_path(path)}"


def _normalize_block(block: str, identity_line: str, slug_fragment: str) -> Tuple[str, bool]:
    """Ensure the host block contains the canonical IdentityFile line."""
    normalized = block if block.endswith("\n") else f"{block}\n"
    lines = normalized.rstrip("\n").split("\n")
    header, *rest = lines
    new_rest = []
    identity_present = False

    for line in rest:
        match = IDENTITY_PATTERN.match(line)
        if not match:
            new_rest.append(line)
            continue

        indent, value = match.groups()
        cleaned = value.strip().strip('"\'' )
        canonical_value = identity_line.split(None, 1)[1]
        if cleaned == canonical_value or slug_fragment in cleaned:
            identity_present = True
            new_rest.append(f"{indent}IdentityFile {canonical_value}")
        else:
            new_rest.append(line)

    if not identity_present:
        new_rest.append(identity_line)

    updated = "\n".join([header] + new_rest)
    if not updated.endswith("\n"):
        updated += "\n"
    return updated, updated != normalized


def _ensure_config_entry(
    account: GitAccount,
    existing_config: str,
    *,
    identity_file: Path,
) -> Tuple[str, bool]:
    """Insert or update the SSH config block for ``account``."""
    new_block = _render_host_block(account, identity_file)
    pattern = _host_pattern(account.ssh_alias)
    match = pattern.search(existing_config)
    if match:
        current_block = match.group(1)
        identity_line = _canonical_identity_line(identity_file)
        slug_fragment = account.alias_slug
        updated_block, changed = _normalize_block(current_block, identity_line, slug_fragment)
        if not changed:
            return existing_config, False
        updated = existing_config[: match.start()] + updated_block + existing_config[match.end() :]
        return updated, True

    updated_config = existing_config.rstrip("\n")
    if updated_config:
        updated_config += "\n"
    updated_config += new_block
    return updated_config, True


def configure_ssh() -> None:
    """Provision per-account SSH identities and update user config."""
    write_known_hosts()
    interactive = sys.stdin.isatty()
    config = get_account_config(interactive=interactive)
    materials = ensure_ssh_materials(config)
    if not materials:
        print("Skipping SSH setup because no keys could be generated.")
        return

    config_text = _load_ssh_config()
    config_text, changed = _synchronise_accounts(config, config_text, materials)
    if changed:
        _write_ssh_config(config_text)

    _add_keys_to_agent(materials)
    outputs = publish_public_materials(materials, {})
    _print_summary(config, outputs, materials)


def _load_ssh_config() -> str:
    if not SSH_CONFIG.exists():
        return ""
    return SSH_CONFIG.read_text()


def _write_ssh_config(config_text: str) -> None:
    cleaned = config_text if config_text.endswith("\n") else f"{config_text}\n"
    SSH_DIR.mkdir(parents=True, exist_ok=True)
    SSH_CONFIG.write_text(cleaned)


def _synchronise_accounts(
    config,
    existing_config: str,
    materials: Dict[str, AccountSshMaterial],
) -> Tuple[str, bool]:
    changed = False
    for account in config.accounts:
        material = materials.get(account.slug)
        if material is None:
            continue
        existing_config, updated = _ensure_config_entry(
            account,
            existing_config,
            identity_file=material.private_key_path,
        )
        changed = changed or updated
    return existing_config, changed


def _add_keys_to_agent(materials: Dict[str, AccountSshMaterial]) -> None:
    for material in materials.values():
        add_result = run(f"ssh-add {shlex.quote(material.private_key_path.as_posix())}")
        if add_result.returncode == 0:
            continue
        message = add_result.stderr.strip() or add_result.stdout.strip() or "unknown error"
        print(f"Failed to add SSH key for {material.account_slug} to ssh-agent: {message}")


def _print_summary(config, outputs, materials) -> None:
    summary = ["\nSSH keys configured locally:"]
    for account in config.accounts:
        material = materials.get(account.slug)
        if material is None:
            continue
        slug_outputs = outputs.get(account.slug, {})
        public_path = slug_outputs.get("ssh_public")
        fingerprint_path = slug_outputs.get("ssh_fingerprint")
        summary.append(f"  - {account.ssh_alias}: {material.private_key_path}")
        if material.fingerprint:
            summary.append(f"    fingerprint: {material.fingerprint}")
        if public_path:
            summary.append(f"    public key: {public_path}")
        if fingerprint_path:
            summary.append(f"    fingerprint file: {fingerprint_path}")
    summary.append("Upload these public keys to your Git hosting services.")
    print("\n".join(summary))

__all__ = ["configure_ssh", "write_known_hosts"]
