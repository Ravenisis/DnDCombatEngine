"""Shared drag-and-drop payload helpers for inventory items."""

from __future__ import annotations

ITEM_MIME_TYPE = "application/x-dnd-combat-inventory-item"


def item_id_from_mime(mime_data) -> str | None:
    """Return an inventory item id from a Qt MIME payload."""
    if mime_data is None or not hasattr(mime_data, "hasFormat"):
        return None
    if not mime_data.hasFormat(ITEM_MIME_TYPE):
        return None
    raw = mime_data.data(ITEM_MIME_TYPE)
    if hasattr(raw, "data"):
        raw = raw.data()
    try:
        value = bytes(raw).decode("utf-8").strip()
    except (TypeError, UnicodeDecodeError):
        return None
    return value or None


def set_item_mime_data(qt, mime_data, item_id: str) -> None:
    """Write an inventory item id to a Qt MIME payload."""
    payload = item_id.encode("utf-8")
    byte_array = getattr(qt.QtCore, "QByteArray", None)
    mime_data.setData(ITEM_MIME_TYPE, byte_array(payload) if byte_array else payload)
