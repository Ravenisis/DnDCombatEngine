"""GUI session helpers for the action bar."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from dnd_combat_engine.models import ActionBar, ActionBarButton


@dataclass(slots=True)
class ActionBarSession:
    """Mutable GUI session wrapper around an action bar model."""

    bar: ActionBar = field(default_factory=ActionBar)
    _listeners: list[Callable[[ActionBar], None]] = field(default_factory=list)

    def subscribe(self, listener: Callable[[ActionBar], None]) -> None:
        """Register a listener that should be called when the bar changes."""
        self._listeners.append(listener)
        listener(self.bar)

    def place(self, button: ActionBarButton) -> str:
        """Place a button on the bar and notify listeners."""
        self.bar = self.bar.place(button)
        self._notify()
        return f"Placed {button.name} on slot {button.slot}."

    def place_next(self, button: ActionBarButton) -> str:
        """Place a button in the next open slot and notify listeners."""
        slot = self.bar.next_open_slot()
        if slot is None:
            return "Action bar is full."
        return self.place(
            ActionBarButton(
                slot=slot,
                kind=button.kind,
                action_id=button.action_id,
                name=button.name,
                rank=button.rank,
                uses_highest_rank=button.uses_highest_rank,
                active_spec=button.active_spec,
                hotkey=button.hotkey,
            )
        )

    def activate(self, slot: int) -> str:
        """Activate a slot and return a user-facing message."""
        return str(self.bar.activate(slot))

    def remove(self, slot: int) -> str:
        """Remove a button from a slot and notify listeners when changed."""
        button = self.bar.button_at(slot)
        if button is None:
            return f"Slot {slot} is already empty."
        self.bar = self.bar.remove(slot)
        self._notify()
        return f"Removed {button.name} from slot {slot}."

    def learn_rank(self, action_id: str, highest_rank: int) -> str:
        """Update highest-rank buttons for a newly learned spell or ability rank."""
        self.bar = self.bar.with_learned_rank(action_id, highest_rank)
        self._notify()
        return f"Learned rank {highest_rank} for {action_id}."

    def _notify(self) -> None:
        for listener in self._listeners:
            listener(self.bar)
