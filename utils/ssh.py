"""SSH configuration helpers for shared key management."""

from __future__ import annotations

import re
import shlex
import sys
import textwrap
from pathlib import Path
from typing import Optional, Tuple

from .accounts import GitAccount, get_account_config
from .debian import run
from .meta import HOME, KNOWN_HOSTS, SSH_CONFIG, SSH_DIR
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
        normalized_current = current_block
        if not normalized_current.endswith("\n"):
            normalized_current += "\n"

        identity_line = f"    IdentityFile {_format_identity_path(identity_path)}"
        identity_value = identity_line.split(None, 1)[1]
        slug_fragment = f"{account.slug}.{account.provider}"
        identity_pattern = re.compile(r"^(\s*)IdentityFile\s+(.+)$", re.IGNORECASE)

        lines = normalized_current.rstrip("\n").split("\n")
        header, *rest = lines
        new_rest = []
        identity_present = False

        for line in rest:
            match_identity = identity_pattern.match(line)
            if not match_identity:
                new_rest.append(line)
                continue

            indent, value = match_identity.groups()
            value = value.strip()
            unquoted = value.strip('"\'')

            if unquoted == identity_value:
                identity_present = True
                new_rest.append(f"{indent}IdentityFile {identity_value}")
                continue

            if slug_fragment in unquoted:
                identity_present = True
                if unquoted != identity_value:
                    new_rest.append(f"{indent}IdentityFile {identity_value}")
                else:
                    new_rest.append(line)
                continue

            new_rest.append(line)

        if not identity_present:
            new_rest.append(identity_line)

        updated_block = "\n".join([header] + new_rest)
        if not updated_block.endswith("\n"):
            updated_block += "\n"

        if updated_block == normalized_current:
            return existing_config, False

        updated = existing_config[: match.start()] + updated_block + existing_config[match.end() :]
        return updated, True

    updated_config = existing_config
    if updated_config and not updated_config.endswith("\n"):
        updated_config += "\n"
    updated_config += new_block
    return updated_config, True


def configure_ssh():
    write_known_hosts()
    interactive = sys.stdin.isatty()
    config = get_account_config(interactive=interactive)
    existing_config = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
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


