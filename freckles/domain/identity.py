from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitIdentity:
    """Value object representing a git identity."""

    slug: str
    provider: str
    display_name: str
    email: str
    directory: Path
    signing_key: str | None = None


@dataclass(frozen=True)
class SshKeyMaterial:
    """Details about an SSH key on disk."""

    private_key: Path
    public_key: Path
    fingerprint: str | None = None


@dataclass(frozen=True)
class GpgKeyMaterial:
    """Details about a GPG key pair."""

    key_id: str
    fingerprint: str | None = None
    public_path: Path | None = None
