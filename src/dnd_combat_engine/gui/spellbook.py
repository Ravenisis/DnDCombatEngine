"""Spellbook and ability-book GUI components."""

from __future__ import annotations

from typing import Any, cast

from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.models.action_bar import ActionBarActionKind, ActionBarButton


class SpellbookWidget:
    """Factory for the spellbook source window."""

    @staticmethod
    def create(
        app: Any,
        qt: Any,
        session: ActionBarSession,
        character_id: str | None = None,
    ) -> Any:
        """Create a spellbook widget that can place spells on the action bar."""
        from dnd_combat_engine.gui import widgets

        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        layout.addWidget(qt.QtWidgets.QLabel(widgets._spellbook_title(app, character_id)))
        tabs = _spellbook_tabs(qt)
        layout.addWidget(tabs)
        attacks_tab = _spellbook_tab(qt)
        spells_tab = _spellbook_tab(qt)
        cantrips_tab = _spellbook_tab(qt)
        abilities_tab = _spellbook_tab(qt)
        channel_tab = _spellbook_tab(qt)
        _add_spellbook_tab(tabs, spells_tab, "Spells")
        _add_spellbook_tab(tabs, abilities_tab, "Abilities")
        _add_spellbook_tab(tabs, cantrips_tab, "Cantrips")
        _add_spellbook_tab(tabs, attacks_tab, "Attacks")
        _add_spellbook_tab(tabs, channel_tab, "Channel Divinity")
        for attack_name in _attack_names_for_character(app, character_id):
            button = qt.QtWidgets.QPushButton(f"{attack_name} (Attack)")
            if hasattr(button, "setToolTip"):
                button.setToolTip(f"Place {attack_name} on the action bar.")
            button.clicked.connect(
                lambda checked=False, name=attack_name: output.append(
                    session.place_next(
                        ActionBarButton(
                            slot=1,
                            kind=ActionBarActionKind.ABILITY,
                            action_id=widgets._action_id(name),
                            name=name,
                            rank=1,
                            uses_highest_rank=True,
                        )
                    )
                )
            )
            _spellbook_tab_add_widget(attacks_tab, button)
        for spell_id in widgets._spell_ids_for_character(app, character_id):
            spell = app.compendium.load_spell(spell_id)
            rank_options = widgets._spell_rank_options(app, character_id, spell)
            highest_rank = max(rank_options)
            for rank in rank_options:
                button = qt.QtWidgets.QPushButton(
                    widgets._spell_rank_button_text(spell.name, rank, spell.level)
                )
                if hasattr(button, "setToolTip"):
                    button.setToolTip(widgets._spell_tooltip(spell, rank))
                button.clicked.connect(
                    lambda checked=False,
                    item=spell,
                    item_rank=rank,
                    item_highest=highest_rank: output.append(
                        session.place_next(
                            ActionBarButton(
                                slot=1,
                                kind=ActionBarActionKind.SPELL,
                                action_id=item.spell_id,
                                name=item.name,
                                rank=item_rank,
                                uses_highest_rank=item_rank == item_highest,
                            )
                        )
                    )
                )
                target_tab = cantrips_tab if spell.level == 0 else spells_tab
                _spellbook_tab_add_widget(target_tab, button)
        for feature in _actionable_ability_names_for_tab(app, character_id):
            button = qt.QtWidgets.QPushButton(feature)
            if hasattr(button, "setToolTip"):
                button.setToolTip(widgets._ability_tooltip(feature))
            button.clicked.connect(
                lambda checked=False, name=feature: output.append(
                    session.place_next(
                        ActionBarButton(
                            slot=1,
                            kind=ActionBarActionKind.ABILITY,
                            action_id=widgets._action_id(name),
                            name=name,
                            rank=1,
                            uses_highest_rank=True,
                        )
                    )
                )
            )
            target_tab = channel_tab if _is_channel_divinity_name(feature) else abilities_tab
            _spellbook_tab_add_widget(target_tab, button)
        for tab in (spells_tab, abilities_tab, cantrips_tab, attacks_tab, channel_tab):
            _spellbook_tab_finish(qt, tab)
        layout.addWidget(output)
        return widget


def _attack_names_for_character(app: Any, character_id: str | None) -> tuple[str, ...]:
    """Return valid weapon and unarmed attacks for a character."""
    from dnd_combat_engine.gui import widgets

    if character_id is None:
        return ()
    try:
        character = app.characters.load(character_id)
    except KeyError:
        return ()
    names = [
        weapon.name
        for weapon in character.weapons
        if widgets._is_valid_attack_name(weapon.name)
    ]
    if "Unarmed Strike" not in names:
        names.append("Unarmed Strike")
    return tuple(names)


def _spellbook_tabs(qt: Any) -> Any:
    tab_class = getattr(qt.QtWidgets, "QTabWidget", None)
    if tab_class is None:
        return _FallbackTabs(qt)
    tabs = tab_class()
    tab_position = getattr(tab_class, "TabPosition", tab_class)
    east = getattr(tab_position, "East", None)
    if east is not None and hasattr(tabs, "setTabPosition"):
        tabs.setTabPosition(east)
    return tabs


class _FallbackTabs:
    def __init__(self, qt: Any) -> None:
        self.widget = qt.QtWidgets.QWidget()
        self.layout = qt.QtWidgets.QVBoxLayout(self.widget)

    def addTab(self, widget: Any, title: str) -> None:  # noqa: N802
        self.layout.addWidget(widget)


def _spellbook_tab(qt: Any) -> Any:
    widget = qt.QtWidgets.QWidget()
    layout = qt.QtWidgets.QVBoxLayout(widget)
    widget._dnd_spellbook_tab_layout = layout  # noqa: SLF001
    widget._dnd_spellbook_tab_count = 0  # noqa: SLF001
    return widget


def _add_spellbook_tab(tabs: Any, tab: Any, title: str) -> None:
    if hasattr(tabs, "addTab"):
        tabs.addTab(tab, title)


def _spellbook_tab_add_widget(tab: Any, widget: Any) -> None:
    layout = getattr(tab, "_dnd_spellbook_tab_layout", None)
    if layout is None:
        return
    layout.addWidget(widget)
    tab._dnd_spellbook_tab_count = getattr(tab, "_dnd_spellbook_tab_count", 0) + 1  # noqa: SLF001


def _spellbook_tab_finish(qt: Any, tab: Any) -> None:
    layout = getattr(tab, "_dnd_spellbook_tab_layout", None)
    if layout is None:
        return
    if getattr(tab, "_dnd_spellbook_tab_count", 0) == 0:
        layout.addWidget(qt.QtWidgets.QLabel("None available"))
    if hasattr(layout, "addStretch"):
        layout.addStretch(1)


def _actionable_ability_names_for_tab(app: Any, character_id: str | None) -> tuple[str, ...]:
    """Return action-ready abilities for the selected character."""
    from dnd_combat_engine.gui import widgets

    if character_id is None:
        return ()
    try:
        character = app.characters.load(character_id)
    except KeyError:
        return ()
    return cast(tuple[str, ...], widgets._actionable_ability_names(character.features))


def _is_channel_divinity_name(name: str) -> bool:
    return name.lower().startswith("channel divinity")
