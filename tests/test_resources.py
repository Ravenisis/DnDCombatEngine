import pytest

from dnd_combat_engine.models import ResourcePool


def test_resource_pool_spends_restores_and_resets() -> None:
    resource = ResourcePool(name="ki", current=3, maximum=5)

    assert resource.expend(2) is True
    assert resource.current == 1
    assert resource.expend(2) is False
    assert resource.restore(10) == 4
    assert resource.current == 5
    resource.current = 0
    resource.reset()
    assert resource.current == 5


def test_resource_pool_caps_current_at_maximum() -> None:
    resource = ResourcePool(name="rage", current=99, maximum=2)

    assert resource.current == 2


def test_resource_pool_round_trips_to_plain_data() -> None:
    resource = ResourcePool(name="spell_slot_1", current=1, maximum=4)

    assert ResourcePool.from_dict(resource.to_dict()) == resource


def test_resource_pool_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        ResourcePool(name="", current=1, maximum=1)
    with pytest.raises(ValueError):
        ResourcePool(name="bardic_inspiration", current=1, maximum=-1)
    with pytest.raises(ValueError):
        ResourcePool(name="bardic_inspiration", current=-1, maximum=1)
    with pytest.raises(ValueError):
        ResourcePool(name="bardic_inspiration", current=1, maximum=1).expend(0)
    with pytest.raises(ValueError):
        ResourcePool(name="bardic_inspiration", current=1, maximum=1).restore(-1)

