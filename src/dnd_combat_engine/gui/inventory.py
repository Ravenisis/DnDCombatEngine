"""Inventory GUI component."""

from __future__ import annotations

from typing import Any


class InventoryWidget:
    """Factory for an RPG-style inventory window."""

    @staticmethod
    def create(
        app: Any,
        qt: Any,
        character_id: str,
        on_consume: Any = None,
        on_sell: Any = None,
        on_currency_change: Any = None,
        on_add_item: Any = None,
        on_move: Any = None,
        money_log_entries: list[str] | None = None,
        money_log_current: dict | None = None,
    ) -> Any:
        """Create an icon inventory grouped by carried containers."""
        from dnd_combat_engine.gui import widgets

        character = app.characters.load(character_id)
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        layout.addWidget(
            widgets._inventory_header(
                qt,
                character.name,
                character.currency,
                on_currency_change,
                on_add_item,
                money_log_entries,
                money_log_current,
            )
        )
        sections = widgets._inventory_storage_sections(character.inventory)
        for container_id, section_name, items in sections:
            layout.addWidget(
                widgets._inventory_section(
                    qt,
                    section_name,
                    items,
                    on_consume,
                    on_sell,
                    on_move,
                    container_id,
                )
            )
        if hasattr(layout, "addStretch"):
            layout.addStretch(1)
        return widget
