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


def get_item(
    vault: str, item: str, *, suppress_missing: bool = False
) -> Optional[Dict]:
    """Return the raw JSON payload for a 1Password item."""

    reference = _item_reference(vault, item)
    result = run(f"op item get {shlex.quote(reference)} --format json")
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        normalized = message.lower()
        if suppress_missing and (
            "isn't an item" in normalized
            or "could not find" in normalized
            or "was not found" in normalized
            or "cannot find" in normalized
        ):
            return None
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
    ensured_sections: set[str] = set()
    temp_files: List[Path] = []
    for field in fields:
        fd, temp_path = tempfile.mkstemp(prefix="freckles-op-")
        os.close(fd)
        path = Path(temp_path)
        temp_files.append(path)
        path.write_text(field.value)
        section_prefix = ""
        if field.section:
            section_prefix = f"{field.section}."
            if field.section not in ensured_sections:
                ensured_sections.add(field.section)
                field_entries.append(
                    shlex.quote(f"{field.section}[label]={field.section}")
                )

        field_identifier = f"{section_prefix}{field.label}"
        field_entries.append(shlex.quote(f"{field_identifier}[label]={field.label}"))
        if field.concealed:
            field_entries.append(shlex.quote(f"{field_identifier}[type]=concealed"))
        field_entries.append(
            shlex.quote(f"{field_identifier}[value]=@{path.as_posix()}"))

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


def _has_section(payload: Dict, label: str) -> bool:
    """Return ``True`` when ``payload`` contains ``label`` section."""

    sections = payload.get("sections")
    if not isinstance(sections, Iterable):
        return False
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_label = (section.get("label") or section.get("name") or "").strip().lower()
        section_id = (section.get("id") or "").strip().lower()
        if label.strip().lower() in {section_label, section_id}:
            return True
    return False


def _create_secure_note(vault: str, item: str) -> bool:
    """Create a secure note for ``vault``/``item`` when it is missing."""

    parts = [
        "op item create",
        "--category",
        shlex.quote("Secure Note"),
        f"--title {shlex.quote(item)}",
    ]
    if vault:
        parts.append(f"--vault {shlex.quote(vault)}")
    command = " ".join(parts)
    result = run(command)
    if result.returncode != 0:
        reference = _item_reference(vault, item)
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(f"Failed to create 1Password item {reference}: {message}")
        return False
    return True


def ensure_ssh_container(vault: str, item: str) -> Optional[Dict]:
    """Ensure ``vault``/``item`` exists with an ``ssh`` section and base fields."""

    payload = get_item(vault, item, suppress_missing=True)
    if payload is None:
        if not _create_secure_note(vault, item):
            return None
        payload = get_item(vault, item, suppress_missing=True)
        if payload is None:
            return None

    placeholders: List[OnePasswordField] = []
    for label, concealed in (
        ("public", False),
        ("private", True),
        ("fingerprint", False),
    ):
        if get_field_value(payload, "ssh", label) is None:
            value = "\n" if label != "fingerprint" else ""
            placeholders.append(
                OnePasswordField(
                    section="ssh",
                    label=label,
                    value=value,
                    concealed=concealed,
                )
            )

    if placeholders:
        if not update_item_fields(vault, item, placeholders):
            return None
        payload = get_item(vault, item, suppress_missing=True)
        if payload is None:
            return None

    # Refresh the payload even if no placeholders were required so that
    # callers always receive the most up-to-date structure, including any
    # newly-created ``ssh`` section.
    if not placeholders:
        refreshed = get_item(vault, item, suppress_missing=True)
        if refreshed is not None:
            payload = refreshed

    return payload
