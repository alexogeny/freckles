"""Helpers for interacting with the 1Password CLI."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from json import JSONDecodeError
from typing import List

from .debian import run


@dataclass
class OnePasswordItem:
    """Lightweight representation of an item in a 1Password vault."""

    title: str
    vault: str
    favorite: bool = False

    def label(self) -> str:
        """Return a human-friendly label describing the item."""

        star = " ★" if self.favorite else ""
        vault = f" ({self.vault})" if self.vault else ""
        return f"{self.title}{vault}{star}".strip()


def ensure_op_connected() -> None:
    """Block until the 1Password CLI is connected to a signed-in account."""

    while run("op account list").stdout == "":
        print("Waiting for connection between op CLI and desktop app...")
        time.sleep(5)


def list_items() -> List[OnePasswordItem]:
    """Return all 1Password items discoverable by the CLI."""

    result = run("op item list --format json")
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(f"Failed to list 1Password items: {message}")
        return []

    try:
        payload = json.loads(result.stdout or "[]")
    except JSONDecodeError as exc:
        print(f"Unable to parse 1Password item list: {exc}")
        return []

    items: List[OnePasswordItem] = []
    for entry in payload:
        vault_info = entry.get("vault") or {}
        vault_name = ""
        if isinstance(vault_info, dict):
            vault_name = vault_info.get("name") or vault_info.get("id") or ""
        items.append(
            OnePasswordItem(
                title=entry.get("title", ""),
                vault=vault_name,
                favorite=bool(entry.get("favorite", False)),
            )
        )

    return items
