#!/usr/bin/env python3
"""Resolve the AWS profile associated with the current working directory."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Iterable, Optional, Tuple

CONFIG_PATH = Path.home() / ".config" / "freckles" / "accounts.json"


def _load_accounts() -> list[dict[str, object]]:
    if not CONFIG_PATH.exists():
        return []
    try:
        data = json.loads(CONFIG_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    accounts = data.get("accounts")
    if isinstance(accounts, list):
        return [account for account in accounts if isinstance(account, dict)]
    return []


def _expand_directory(directory: str) -> Path:
    expanded = os.path.expanduser(directory)
    try:
        return Path(expanded).resolve()
    except OSError:
        return Path(expanded)


def _git_root() -> Optional[Path]:
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    path = output.decode().strip()
    if not path:
        return None
    return Path(path).resolve()


def _candidate_paths() -> Iterable[Path]:
    cwd = Path.cwd()
    try:
        cwd = cwd.resolve()
    except OSError:
        pass
    yield cwd
    root = _git_root()
    if root:
        yield root


def _matches(base: Path, candidate: Path) -> bool:
    if base == candidate:
        return True
    try:
        candidate.relative_to(base)
    except ValueError:
        return False
    return True


def _determine_profile() -> Optional[str]:
    accounts = _load_accounts()
    if not accounts:
        return None

    candidates = list(_candidate_paths())
    best_match: Optional[Tuple[int, str]] = None

    for account in accounts:
        profile = account.get("aws_profile")
        directory = account.get("directory")
        if not profile or not isinstance(profile, str):
            continue
        if not directory or not isinstance(directory, str):
            continue
        base = _expand_directory(directory)
        base_posix = base.as_posix()
        for candidate in candidates:
            if _matches(base, candidate):
                score = len(base_posix)
                if not best_match or score > best_match[0]:
                    best_match = (score, profile)
                break

    if best_match:
        return best_match[1]
    return None


def main() -> int:
    profile = _determine_profile()
    if profile:
        print(profile.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
