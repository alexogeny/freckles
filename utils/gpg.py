"""Helpers to discover, generate, and export GPG key material."""

from __future__ import annotations

import shlex
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .debian import run


@dataclass
class GpgMaterial:
    """Container for exported GPG key material."""

    key_id: str
    fingerprint: str
    public_key: str
    private_key: str


def _parse_secret_key(output: str) -> Optional[Tuple[str, str]]:
    """Extract the key id and fingerprint from ``gpg --with-colons`` output."""

    key_id: Optional[str] = None
    fingerprint: Optional[str] = None
    for line in output.splitlines():
        parts = line.split(":")
        if not parts:
            continue
        record_type = parts[0]
        if record_type == "sec" and len(parts) > 4:
            key_id = parts[4]
        elif record_type == "fpr" and len(parts) > 9 and fingerprint is None:
            fingerprint = parts[9]
    if key_id and fingerprint:
        return key_id, fingerprint
    if key_id:
        return key_id, ""
    return None


def discover_secret_key(query: str) -> Optional[Tuple[str, str]]:
    """Return the key id and fingerprint for a matching secret key."""

    command = f"gpg --list-secret-keys --with-colons --fingerprint {shlex.quote(query)}"
    result = run(command)
    if result.returncode != 0:
        return None
    return _parse_secret_key(result.stdout or "")


def generate_secret_key(name: str, email: str) -> Optional[Tuple[str, str]]:
    """Generate a new secret key for the supplied identity."""

    template = """
Key-Type: eddsa
Key-Curve: ed25519
Subkey-Type: cv25519
Subkey-Curve: cv25519
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
%no-protection
%commit
""".strip().format(name=name, email=email)

    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        template_path = Path(handle.name)
        handle.write(template)

    command = f"gpg --batch --generate-key {shlex.quote(template_path.as_posix())}"
    result = run(command)
    template_path.unlink(missing_ok=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(
            f"Failed to generate GPG key for {name} ({email}): {message}"
        )
        return None

    lookup = discover_secret_key(email)
    if lookup is None:
        return None
    return lookup


def export_gpg_material(key_id: str) -> Optional[GpgMaterial]:
    """Export public and private key material for ``key_id``."""

    public_result = run(f"gpg --armor --export {key_id}")
    if public_result.returncode != 0:
        message = public_result.stderr.strip() or public_result.stdout.strip() or "unknown error"
        print(f"Failed to export public GPG key {key_id}: {message}")
        return None

    private_result = run(f"gpg --armor --export-secret-keys {key_id}")
    if private_result.returncode != 0:
        message = private_result.stderr.strip() or private_result.stdout.strip() or "unknown error"
        print(f"Failed to export private GPG key {key_id}: {message}")
        return None

    fingerprint_result = run(
        f"gpg --with-colons --fingerprint {key_id}"
    )
    fingerprint = ""
    if fingerprint_result.returncode == 0:
        parsed = _parse_secret_key(fingerprint_result.stdout or "")
        if parsed:
            fingerprint = parsed[1]

    return GpgMaterial(
        key_id=key_id,
        fingerprint=fingerprint,
        public_key=(public_result.stdout or "").strip(),
        private_key=(private_result.stdout or "").strip(),
    )
