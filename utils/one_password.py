"""Helpers for interacting with the 1Password CLI."""

from __future__ import annotations

import json
import os
import shlex
import tempfile
import time
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Iterable, List, Optional

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


@dataclass
class OnePasswordField:
    """Representation of a 1Password field update."""

    label: str
    value: str
    section: Optional[str] = None
    concealed: bool = False


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


def _item_reference(vault: str, item: str) -> str:
    if not vault:
        return item
    return f"{vault}/{item}"


def get_item(vault: str, item: str) -> Optional[Dict]:
    """Return the raw JSON payload for a 1Password item."""

    reference = _item_reference(vault, item)
    result = run(f"op item get {shlex.quote(reference)} --format json")
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(f"Failed to fetch 1Password item {reference}: {message}")
        return None

    try:
        return json.loads(result.stdout or "{}")
    except JSONDecodeError as exc:
        print(f"Unable to parse 1Password item {reference}: {exc}")
        return None


def _field_matches(field: Dict, section: Optional[str], label: str) -> bool:
    field_label = (field.get("label") or field.get("name") or "").strip().lower()
    target_label = (label or "").strip().lower()
    if field_label != target_label:
        return False
    if not section:
        return True
    section_info = field.get("section") or {}
    section_id = ""
    if isinstance(section_info, dict):
        section_id = (section_info.get("id") or section_info.get("label") or "").strip().lower()
    return section_id == section.strip().lower()


def get_field_value(item: Dict, section: Optional[str], label: str) -> Optional[str]:
    """Return the value of ``label`` inside ``section`` when available."""

    fields = item.get("fields") if isinstance(item, dict) else None
    if not isinstance(fields, Iterable):
        return None
    for field in fields:
        if not isinstance(field, dict):
            continue
        if _field_matches(field, section, label):
            value = field.get("value")
            if value is None:
                continue
            return str(value)
    return None


def update_item_fields(vault: str, item: str, fields: Iterable[OnePasswordField]) -> bool:
    """Update or create fields on a 1Password item.

    Multi-line values are written to temporary files to avoid shell quoting
    pitfalls when invoking the CLI.
    """

    field_entries = []
    temp_files: List[Path] = []
    for field in fields:
        fd, temp_path = tempfile.mkstemp(prefix="freckles-op-")
        os.close(fd)
        path = Path(temp_path)
        temp_files.append(path)
        path.write_text(field.value)
        parts = []
        if field.section:
            parts.append(f"section={field.section}")
        parts.append(f"label={field.label}")
        if field.concealed:
            parts.append("type=concealed")
        parts.append(f"value@={path.as_posix()}")
        field_entries.append(f"--field {shlex.quote(' '.join(parts))}")

    reference = _item_reference(vault, item)
    command = " ".join([f"op item edit {shlex.quote(reference)}"] + field_entries)
    result = run(command)

    for path in temp_files:
        try:
            os.unlink(path)
        except OSError:
            pass

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(f"Failed to update 1Password item {reference}: {message}")
        return False

    return True
