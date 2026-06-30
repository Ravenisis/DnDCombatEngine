"""Action bar models for quick spell and ability activation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Self


class ActionBarActionKind(StrEnum):
    """Kinds of entries that can be placed on the action bar."""

    SPELL = "spell"
    ABILITY = "ability"


@dataclass(frozen=True, slots=True)
class ActionBarButton:
    """One spell or ability assigned to an action bar slot."""

    slot: int
    kind: ActionBarActionKind
    action_id: str
    name: str
    rank: int = 1
    uses_highest_rank: bool = True
    active_spec: bool = True
    hotkey: str | None = None

    def __post_init__(self) -> None:
        """Validate the slot assignment."""
        if self.slot < 1:
            raise ValueError("slot must be at least 1")
        if not self.action_id:
            raise ValueError("action_id is required")
        if not self.name:
            raise ValueError("name is required")
        if self.rank < 1:
            raise ValueError("rank must be at least 1")

    def with_learned_rank(self, highest_rank: int) -> Self:
        """Return a rank-updated button when this button tracks the highest rank."""
        if highest_rank < 1:
            raise ValueError("highest_rank must be at least 1")
        if not self.active_spec or not self.uses_highest_rank or highest_rank <= self.rank:
            return self
        return replace(self, rank=highest_rank)

    @property
    def label(self) -> str:
        """Return compact display text for the action bar."""
        rank_text = f" R{self.rank}" if self.rank > 1 else ""
        return f"{self.hotkey or self.slot}\n{self.name}{rank_text}"


@dataclass(frozen=True, slots=True)
class ActionBar:
    """A fixed-size quick action bar."""

    slot_count: int = 12
    buttons: tuple[ActionBarButton, ...] = ()

    def __post_init__(self) -> None:
        """Validate slot bounds and uniqueness."""
        if self.slot_count < 1:
            raise ValueError("slot_count must be at least 1")
        slots = [button.slot for button in self.buttons]
        if any(slot > self.slot_count for slot in slots):
            raise ValueError("button slot cannot exceed slot_count")
        if len(set(slots)) != len(slots):
            raise ValueError("action bar slots cannot contain duplicates")

    def button_at(self, slot: int) -> ActionBarButton | None:
        """Return the button assigned to a slot, if any."""
        return next((button for button in self.buttons if button.slot == slot), None)

    def next_open_slot(self) -> int | None:
        """Return the first empty slot number, if one exists."""
        occupied = {button.slot for button in self.buttons}
        return next((slot for slot in range(1, self.slot_count + 1) if slot not in occupied), None)

    def place(self, button: ActionBarButton) -> Self:
        """Return an action bar with a button assigned to its slot."""
        if button.slot > self.slot_count:
            raise ValueError("button slot cannot exceed slot_count")
        buttons = tuple(item for item in self.buttons if item.slot != button.slot)
        return replace(self, buttons=tuple(sorted((*buttons, button), key=lambda item: item.slot)))

    def remove(self, slot: int) -> Self:
        """Return an action bar with a slot cleared."""
        if slot < 1:
            raise ValueError("slot must be at least 1")
        if slot > self.slot_count:
            raise ValueError("button slot cannot exceed slot_count")
        return replace(self, buttons=tuple(item for item in self.buttons if item.slot != slot))

    def activate(self, slot: int) -> str:
        """Return a user-facing activation message for a slot."""
        button = self.button_at(slot)
        if button is None:
            return f"Slot {slot} is empty."
        return f"Activated {button.name} rank {button.rank}."

    def with_learned_rank(self, action_id: str, highest_rank: int) -> Self:
        """Return an action bar after learning a new highest rank for an action."""
        return replace(
            self,
            buttons=tuple(
                button.with_learned_rank(highest_rank)
                if button.action_id == action_id
                else button
                for button in self.buttons
            ),
        )
