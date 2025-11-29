"""Secret management helpers (1Password CLI)."""

from .one_password import (
    OnePasswordField,
    OnePasswordItem,
    MultipleItemsFoundError,
    ensure_op_connected,
    list_items,
    resolve_item_identifier,
    fetch_item_json,
    update_item_fields,
    create_item,
)

__all__ = [
    "OnePasswordField",
    "OnePasswordItem",
    "MultipleItemsFoundError",
    "ensure_op_connected",
    "list_items",
    "resolve_item_identifier",
    "fetch_item_json",
    "update_item_fields",
    "create_item",
]
