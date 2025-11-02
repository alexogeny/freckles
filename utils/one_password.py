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

from .debian import run


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

    normalised_vault = (vault or "").strip().lower()
    items = catalog if catalog is not None else list_items()
    matches: List[OnePasswordItem] = []
    for entry in items:
        if normalised_vault:
            vault_aliases = {
                alias.strip().lower()
                for alias in (entry.vault, entry.vault_id)
                if alias
            }
            if vault_aliases:
                if normalised_vault not in vault_aliases:
                    continue
            elif entry.vault.strip().lower() != normalised_vault:
                continue
        if entry.title.strip().lower() == candidate.lower():
            matches.append(entry)

    if not matches:
        return None

    if len(matches) == 1:
        identifier = matches[0].identifier.strip()
        return identifier or None

    exact_case = [match for match in matches if match.title.strip() == candidate]
    if len(exact_case) == 1:
        identifier = exact_case[0].identifier.strip()
        return identifier or None

    favourites = [match for match in matches if match.favorite and match.identifier.strip()]
    if len(favourites) == 1:
        return favourites[0].identifier.strip()

    raise MultipleItemsFoundError(vault, item, matches)


def _item_reference(vault: str, item: str) -> str:
    if not vault:
        return item
    return f"{vault}/{item}"


def _item_command_args(vault: str, item: str) -> List[str]:
    args: List[str] = []
    if vault:
        args.extend(["--vault", shlex.quote(vault)])
    args.append(shlex.quote(item))
    return args


def get_item(
    vault: str, item: str, *, suppress_missing: bool = False
) -> Optional[Dict]:
    """Return the raw JSON payload for a 1Password item."""

    reference = _item_reference(vault, item)
    try:
        resolved_item = resolve_item_identifier(vault, item)
    except MultipleItemsFoundError as exc:
        print(
            "Failed to resolve a unique 1Password item for "
            f"{reference}. Multiple items matched the provided name."
        )
        for match in exc.matches:
            print(f"  - {match.label()} [{match.identifier}]")
        print("Please update the configuration to reference the desired item by ID.")
        return None
    if resolved_item is None and item:
        print(
            "Failed to locate 1Password item "
            f"{reference}. Please verify the vault and item names."
        )
        return None

    command_parts = [
        "op item get",
        *_item_command_args(vault, resolved_item or item),
        "--format",
        "json",
    ]
    result = run(" ".join(command_parts))
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

    field_list = list(fields)
    if not field_list:
        return True

    try:
        resolved_item = resolve_item_identifier(vault, item)
    except MultipleItemsFoundError as exc:
        reference = _item_reference(vault, item)
        print(
            "Failed to resolve a unique 1Password item for "
            f"{reference}. Multiple items matched the provided name."
        )
        for match in exc.matches:
            print(f"  - {match.label()} [{match.identifier}]")
        print("Please update the configuration to reference the desired item by ID.")
        return False
    if resolved_item is None:
        reference = _item_reference(vault, item)
        print(
            "Failed to locate 1Password item "
            f"{reference}. Please verify the vault and item names."
        )
        return False

    reference = _item_reference(vault, item)
    for field in field_list:
        fd, temp_path = tempfile.mkstemp(prefix="freckles-op-")
        os.close(fd)
        path = Path(temp_path)
        path.write_text(field.value)
        section_prefix = f"{field.section}." if field.section else ""
        field_identifier = f"{section_prefix}{field.label}"
        type_suffix = "[concealed]" if field.concealed else ""
        field_entry = shlex.quote(
            f"{field_identifier}{type_suffix}=@{path.as_posix()}"
        )

        command_parts = [
            "op item edit",
            *_item_command_args(vault, resolved_item),
            field_entry,
        ]
        command = " ".join(command_parts)
        result = run(command)

        try:
            os.unlink(path)
        except OSError:
            pass

        if result.returncode != 0:
            message = (
                result.stderr.strip() or result.stdout.strip() or "unknown error"
            )
            print(f"Failed to update 1Password item {reference}: {message}")
            normalized = message.lower()
            if "panic" in normalized or "sigsegv" in normalized or "segmentation" in normalized:
                print(
                    "The 1Password CLI encountered an unexpected crash while editing "
                    f"{reference}. Ensure the desktop app and CLI are up to date, "
                    "then retry the operation. If the issue persists, update the "
                    "fields manually in 1Password."
                )
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


def ensure_ssh_container(
    vault: str,
    item: str,
    *,
    create_if_missing: bool = True,
    initial_fields: Optional[Iterable[OnePasswordField]] = None,
) -> Optional[Dict]:
    """Ensure ``vault``/``item`` exists with an ``ssh`` section and base fields."""

    payload = get_item(vault, item, suppress_missing=True)
    if payload is None:
        if not create_if_missing:
            reference = _item_reference(vault, item)
            print(
                "Unable to locate 1Password item "
                f"{reference}. Please create it manually before continuing."
            )
            return None
        if not _create_secure_note(vault, item):
            return None
        field_seed = list(initial_fields or [])
        if field_seed:
            if not update_item_fields(vault, item, field_seed):
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
