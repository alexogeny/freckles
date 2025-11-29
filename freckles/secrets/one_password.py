"""Helpers for interacting with the 1Password CLI."""

from __future__ import annotations

import json
import os
import re
import shlex
import tempfile
import time
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from freckles.system.debian import run


@dataclass
class OnePasswordItem:
    """Lightweight representation of an item in a 1Password vault."""

    title: str
    vault: str
    identifier: str
    favorite: bool = False
    vault_id: str = ""

    def label(self) -> str:
        """Return a human-friendly label describing the item."""

        star = " ★" if self.favorite else ""
        vault = f" ({self.vault})" if self.vault else ""
        return f"{self.title}{vault}{star}".strip()


@dataclass
class OnePasswordField:
    """Representation of a 1Password field update."""

    label: str
    value: str
    section: Optional[str] = None
    concealed: bool = False
    kind: Optional[str] = "text"


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
        vault_id = ""
        if isinstance(vault_info, dict):
            vault_name = vault_info.get("name") or ""
            vault_id = vault_info.get("id") or ""
            if not vault_name:
                vault_name = vault_id
        items.append(
            OnePasswordItem(
                title=entry.get("title", ""),
                vault=vault_name,
                identifier=entry.get("id", ""),
                favorite=bool(entry.get("favorite", False)),
                vault_id=vault_id,
            )
        )

    return items


class MultipleItemsFoundError(Exception):
    """Raised when more than one 1Password item matches a query."""

    def __init__(self, vault: str, item: str, matches: List[OnePasswordItem]):
        self.vault = vault
        self.item = item
        self.matches = matches
        resolved_vault = vault or "default"
        super().__init__(
            f"Multiple items matched '{item}' in vault '{resolved_vault}'."
        )


_ITEM_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]{26}$")


def _is_item_identifier(value: str) -> bool:
    return bool(value) and bool(_ITEM_IDENTIFIER_PATTERN.fullmatch(value))


def resolve_item_identifier(
    vault: str, item: str, catalog: Optional[List[OnePasswordItem]] = None
) -> Optional[str]:
    """Return the stable identifier for ``item`` within ``vault`` when possible."""

    candidate = (item or "").strip()
    if _is_item_identifier(candidate):
        return candidate

    items = catalog or list_items()
    vault = vault.strip() if vault else ""
    matches = []
    for entry in items:
        if vault and vault not in {entry.vault, entry.vault_id}:
            continue
        if entry.title.lower() == candidate.lower():
            matches.append(entry)

    if not matches:
        return None
    if len(matches) == 1:
        return matches[0].identifier
    raise MultipleItemsFoundError(vault, item, matches)


def fetch_item_json(reference: str) -> Optional[Dict]:
    """Return the raw JSON payload for a 1Password item."""

    result = run(f"op item get {shlex.quote(reference)} --format json")
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(f"Failed to locate 1Password item {reference}: {message}")
        return None

    try:
        return json.loads(result.stdout or "{}")
    except JSONDecodeError as exc:
        print(f"Unable to parse 1Password item {reference}: {exc}")
        return None


def update_item_fields(
    reference: str,
    fields: Iterable[OnePasswordField],
    *,
    vault: Optional[str] = None,
) -> bool:
    """Update or create fields on a 1Password item."""

    items = list_items()
    vault = vault or ""
    identifier = resolve_item_identifier(vault, reference, catalog=items)
    if not identifier:
        print(
            "Failed to resolve a unique 1Password item for "
            f"{reference} in vault {vault or 'default'}"
        )
        return False

    input_fields: list[str] = []
    for field in fields:
        parts = ["label=" + field.label, "value=" + field.value]
        if field.section:
            parts.append("section=" + field.section)
        if field.concealed:
            parts.append("type=concealed")
        elif field.kind:
            parts.append("type=" + field.kind)
        input_fields.append(",".join(parts))

    quoted_fields = " ".join(shlex.quote(part) for part in input_fields)
    command = f"op item edit {shlex.quote(identifier)} {quoted_fields}"
    if vault:
        command += f" --vault {shlex.quote(vault)}"

    result = run(command)
    if result.returncode == 0:
        return True
    if result.returncode == 1 and "The 1Password CLI encountered an unexpected crash" in (result.stderr or ""):
        print(
            "The 1Password CLI encountered an unexpected crash while editing "
            "fields manually in 1Password."
        )
    else:
        print(f"Failed to update 1Password item {reference}: {result.stderr or result.stdout}")
    return False


def create_item(
    vault: str,
    title: str,
    category: str,
    fields: Iterable[OnePasswordField],
    *,
    tags: Optional[List[str]] = None,
) -> Optional[str]:
    """Create a 1Password item and return its identifier."""

    command = [
        "op",
        "item",
        "create",
        "--vault",
        vault,
        "--category",
        category,
        "--title",
        title,
    ]
    for field in fields:
        command.extend(
            ["--field", f"label={field.label},value={field.value},type={'concealed' if field.concealed else field.kind}"]
        )
    if tags:
        for tag in tags:
            command.extend(["--tag", tag])

    with tempfile.NamedTemporaryFile("w", delete=False) as temp_file:
        temp_file.write("{}")
        temp_path = Path(temp_file.name)

    command.extend(["--generate-password", f"file={temp_path}"])

    result = run(" ".join(shlex.quote(part) for part in command))
    temp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(f"Failed to create 1Password item {title}: {message}")
        return None

    try:
        payload = json.loads(result.stdout or "{}")
        identifier = payload.get("id")
        return identifier if isinstance(identifier, str) else None
    except JSONDecodeError as exc:
        print(f"Unable to parse 1Password create response: {exc}")
        return None

