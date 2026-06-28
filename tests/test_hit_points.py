import pytest

from dnd_combat_engine.models import HitPoints


def test_damage_consumes_temporary_hit_points_first() -> None:
    hit_points = HitPoints(current=10, maximum=10, temporary=5)

    lost_current = hit_points.apply_damage(7)

    assert lost_current == 2
    assert hit_points.temporary == 0
    assert hit_points.current == 8


def test_current_hit_points_are_capped_at_maximum() -> None:
    assert HitPoints(current=20, maximum=10).current == 10


def test_consciousness_reflects_current_hit_points() -> None:
    assert HitPoints(current=1, maximum=10).is_conscious is True
    assert HitPoints(current=0, maximum=10).is_conscious is False


def test_temporary_hit_points_do_not_stack() -> None:
    hit_points = HitPoints(current=10, maximum=10, temporary=5)

    assert hit_points.grant_temporary(3) is False
    assert hit_points.temporary == 5
    assert hit_points.grant_temporary(8) is True
    assert hit_points.temporary == 8


def test_healing_does_not_exceed_maximum() -> None:
    hit_points = HitPoints(current=2, maximum=10)

    restored = hit_points.heal(50)

    assert restored == 8
    assert hit_points.current == 10


def test_hit_points_reject_negative_damage() -> None:
    with pytest.raises(ValueError):
        HitPoints(current=10, maximum=10).apply_damage(-1)


def test_hit_points_reject_invalid_values() -> None:
    with pytest.raises(ValueError):
        HitPoints(current=1, maximum=0)
    with pytest.raises(ValueError):
        HitPoints(current=-1, maximum=10)
    with pytest.raises(ValueError):
        HitPoints(current=1, maximum=10, temporary=-1)
    with pytest.raises(ValueError):
        HitPoints(current=1, maximum=10).heal(-1)
    with pytest.raises(ValueError):
        HitPoints(current=1, maximum=10).grant_temporary(-1)
