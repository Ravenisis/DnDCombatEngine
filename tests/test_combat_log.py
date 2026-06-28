import pytest

from dnd_combat_engine.models import CombatLog, CombatLogEntry, CombatLogEntryType


def test_combat_log_entry_round_trips_to_plain_data() -> None:
    entry = CombatLogEntry(
        "Vale hits Goblin.",
        CombatLogEntryType.ATTACK,
        metadata={"damage": 7},
    )

    restored = CombatLogEntry.from_dict(entry.to_dict())

    assert restored == entry


def test_combat_log_appends_and_returns_latest_entries() -> None:
    first = CombatLogEntry("First")
    second = CombatLogEntry("Second")
    log = CombatLog().append(first).append(second)

    assert log.latest(1) == (second,)
    assert CombatLog.from_dict(log.to_dict()) == log


def test_combat_log_validates_values() -> None:
    with pytest.raises(ValueError):
        CombatLogEntry("")
    with pytest.raises(ValueError):
        CombatLog().latest(0)

