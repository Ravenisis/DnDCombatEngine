from types import SimpleNamespace

from dnd_combat_engine.gui import main_window
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.models import (
    ActionBar,
    ActionBarActionKind,
    ActionBarButton,
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    ResourcePool,
    Spell,
    SpellSchool,
    Weapon,
)


class FakeDice:
    def __init__(self, total: int = 7) -> None:
        self.total = total
        self.notations = []

    def roll(self, notation: str):
        self.notations.append(notation)
        return SimpleNamespace(notation=notation, total=self.total, rolls=(self.total,))


class FakeStatusBar:
    def __init__(self) -> None:
        self.message = ""

    def showMessage(self, message: str) -> None:
        self.message = message


class FakeWorkspace:
    def __init__(self) -> None:
        self.messages = []

    def append(self, message: str) -> None:
        self.messages.append(message)


class FakeWindow:
    def __init__(self) -> None:
        self._dnd_central = FakeWorkspace()
        self.status = FakeStatusBar()

    def statusBar(self):
        return self.status


class FakeTextTarget:
    def __init__(self) -> None:
        self.text = ""

    def setText(self, message: str) -> None:  # noqa: N802
        self.text = message


class FakeCharacters:
    def __init__(self, character: Character) -> None:
        self.character = character
        self.saved = []

    def load(self, character_id: str) -> Character:
        assert character_id == self.character.character_id
        return self.character

    def save(self, character: Character) -> None:
        self.saved.append(character)


class FakeCompendium:
    def __init__(self, spell: Spell) -> None:
        self.spell = spell

    def load_spell(self, spell_id: str) -> Spell:
        assert spell_id == self.spell.spell_id
        return self.spell


def _raise_key_error(*args):
    raise KeyError


def _spell(spell_id: str = "guiding_bolt", level: int = 1, damage=None) -> Spell:
    return Spell(
        spell_id=spell_id,
        name="Guiding Bolt",
        level=level,
        school=SpellSchool.EVOCATION,
        casting_time="1 action",
        range_text="120 feet",
        duration="Instantaneous",
        damage=damage,
    )


def _app(character: Character, spell: Spell | None = None, total: int = 7):
    return SimpleNamespace(
        characters=FakeCharacters(character),
        compendium=FakeCompendium(spell or _spell()),
        dice=FakeDice(total),
    )


def test_spell_action_rolls_damage_and_spends_spell_slot() -> None:
    character = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_1": ResourcePool("spell_slot_1", 1, 1)},
    )
    spell = _spell(
        damage=DamageProfile((DamageComponent("4d6", DamageType.RADIANT),)),
    )
    app = _app(character, spell)
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "guiding_bolt", "Guiding Bolt")

    message = main_window._activate_spell_button(app, character, button)

    assert "Cleric casts Guiding Bolt" in message
    assert "Damage 7" in message
    assert "Used level 1 spell slot; 0/1 remain." in message
    assert character.resources["spell_slot_1"].current == 0
    assert app.characters.saved == [character]


def test_spell_action_reports_missing_slots_before_rolling() -> None:
    character = Character("cleric", "Cleric", HitPoints(20, 20))
    app = _app(character, _spell())
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "guiding_bolt", "Guiding Bolt")

    message = main_window._activate_spell_button(app, character, button)

    assert message == "Cleric cannot cast Guiding Bolt: no level 1 slots."
    assert app.dice.notations == []


def test_spell_action_reports_depleted_slots_and_non_damage_spells() -> None:
    character = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_1": ResourcePool("spell_slot_1", 0, 1)},
    )
    app = _app(character, _spell(damage=None))
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "guiding_bolt", "Guiding Bolt")

    assert main_window._activate_spell_button(app, character, button) == (
        "Cleric cannot cast Guiding Bolt: no level 1 slots remaining."
    )

    character.resources["spell_slot_1"].current = 1
    message = main_window._activate_spell_button(app, character, button)

    assert "No damage dice configured." in message
    assert "Used level 1 spell slot; 0/1 remain." in message


def test_cantrip_action_rolls_damage_without_spending_slots() -> None:
    character = Character("cleric", "Cleric", HitPoints(20, 20))
    spell = _spell(
        spell_id="sacred_flame",
        level=0,
        damage=DamageProfile((DamageComponent("1d8", DamageType.RADIANT),)),
    )
    app = _app(character, spell)
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "sacred_flame", "Sacred Flame")

    message = main_window._activate_spell_button(app, character, button)

    assert "Damage 7" in message
    assert "No spell slot used." in message
    assert app.characters.saved == []


def test_ability_action_rolls_first_weapon_damage() -> None:
    character = Character(
        "fighter",
        "Fighter",
        HitPoints(20, 20),
        weapons=(
            Weapon(
                "Longsword",
                DamageProfile((DamageComponent("1d8", DamageType.SLASHING),)),
            ),
        ),
    )
    app = _app(character)
    button = ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack", rank=2)

    message = main_window._activate_ability_button(app, character, button)

    assert "Fighter uses Attack with Longsword rank 2" in message
    assert "1d8 slashing" in message


def test_action_activation_handles_empty_selection_and_missing_data() -> None:
    character = Character("fighter", "Fighter", HitPoints(20, 20))
    app = _app(character)
    button = ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack")

    assert main_window._activate_action_button(app, main_window.GuiCampaignState(), None) == (
        "Action slot is empty."
    )
    assert main_window._activate_action_button(
        app,
        main_window.GuiCampaignState(selected_character_id=None),
        button,
    ) == "Select a character before using Attack."
    assert main_window._activate_action_button(
        SimpleNamespace(characters=SimpleNamespace(load=_raise_key_error)),
        main_window.GuiCampaignState(selected_character_id="missing"),
        button,
    ) == "Selected character missing could not be loaded."


def test_spell_action_reports_missing_compendium_entry() -> None:
    character = Character("cleric", "Cleric", HitPoints(20, 20))
    app = SimpleNamespace(compendium=SimpleNamespace(load_spell=_raise_key_error))
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "missing", "Missing")

    assert main_window._activate_spell_button(app, character, button) == (
        "Missing is not in the spell compendium."
    )


def test_ability_action_reports_missing_weapon_and_workspace_set_text_fallback() -> None:
    character = Character("fighter", "Fighter", HitPoints(20, 20))
    app = _app(character)
    button = ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack")

    assert main_window._activate_ability_button(app, character, button) == (
        "Fighter uses Attack. No attack damage dice configured."
    )

    window = SimpleNamespace(_dnd_central=FakeTextTarget())
    main_window._append_workspace(window, "Logged")
    assert window._dnd_central.text == "Logged"


def test_shift_action_bar_activation_rolls_d20_in_workspace(monkeypatch) -> None:
    window = FakeWindow()
    character = Character("cleric", "Cleric", HitPoints(20, 20))
    app = _app(character, total=13)
    state = main_window.GuiCampaignState(selected_character_id="cleric")
    session = ActionBarSession(ActionBar())
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    message = main_window._activate_action_bar_slot(
        window,
        object(),
        app,
        state,
        session,
        1,
        True,
    )

    assert message == "Slot 1 d20: 13 rolls=(13,)"
    assert window._dnd_central.messages == [message]
    assert window.status.message == message


def test_normal_action_bar_activation_logs_result_and_refreshes(monkeypatch) -> None:
    window = FakeWindow()
    character = Character(
        "fighter",
        "Fighter",
        HitPoints(20, 20),
        weapons=(
            Weapon(
                "Longsword",
                DamageProfile((DamageComponent("1d8", DamageType.SLASHING),)),
            ),
        ),
    )
    app = _app(character, total=5)
    state = main_window.GuiCampaignState(selected_character_id="fighter")
    session = ActionBarSession(
        ActionBar(
            buttons=(ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack"),)
        )
    )
    refresh_calls = []
    monkeypatch.setattr(
        main_window,
        "_refresh_campaign_docks",
        lambda *args: refresh_calls.append(args),
    )

    message = main_window._activate_action_bar_slot(
        window,
        object(),
        app,
        state,
        session,
        1,
        False,
    )

    assert "Fighter uses Attack with Longsword" in message
    assert window._dnd_central.messages == [message]
    assert window.status.message == message
    assert len(refresh_calls) == 1
