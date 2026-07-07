from fractions import Fraction
from types import SimpleNamespace

from dnd_combat_engine.gui import main_window
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.models import (
    AbilityScores,
    ActionBar,
    ActionBarActionKind,
    ActionBarButton,
    Campaign,
    Character,
    ConcentrationState,
    Condition,
    ConditionName,
    DamageComponent,
    DamageProfile,
    DamageType,
    EffectDefinition,
    EffectKind,
    Encounter,
    EncounterParticipant,
    HitPoints,
    Monster,
    ParticipantKind,
    ResourcePool,
    Spell,
    SpellSchool,
    TargetKind,
    TargetProfile,
    TargetReference,
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


class FakeCharacterStore:
    def __init__(self, characters: tuple[Character, ...]) -> None:
        self.characters = {character.character_id: character for character in characters}
        self.saved = []

    def load(self, character_id: str) -> Character:
        return self.characters[character_id]

    def save(self, character: Character) -> None:
        self.saved.append(character)


class FakeCompendium:
    def __init__(self, spell: Spell, monster: Monster | None = None) -> None:
        self.spell = spell
        self.monster = monster

    def load_spell(self, spell_id: str) -> Spell:
        assert spell_id == self.spell.spell_id
        return self.spell

    def load_monster(self, monster_id: str) -> Monster:
        assert self.monster is not None
        assert monster_id == self.monster.monster_id
        return self.monster


class FakeEncounterStore:
    def __init__(self, encounter: Encounter) -> None:
        self.encounter = encounter
        self.saved = []
        self.persistence_service = SimpleNamespace(
            list_encounter_ids=lambda: [self.encounter.encounter_id]
        )

    def load(self, encounter_id: str) -> Encounter:
        assert encounter_id == self.encounter.encounter_id
        return self.encounter

    def save(self, encounter: Encounter) -> None:
        self.encounter = encounter
        self.saved.append(encounter)


class FakeCampaignStore:
    def __init__(self, campaign: Campaign) -> None:
        self.campaign = campaign
        self.saved = []

    def load(self, campaign_id: str) -> Campaign:
        assert campaign_id == self.campaign.campaign_id
        return self.campaign

    def save(self, campaign: Campaign) -> None:
        self.campaign = campaign
        self.saved.append(campaign)


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


def _beacon_spell() -> Spell:
    return Spell(
        spell_id="beacon_of_hope",
        name="Beacon of Hope",
        level=3,
        school=SpellSchool.ABJURATION,
        casting_time="1 action",
        range_text="30 feet",
        duration="Concentration, up to 1 minute",
        concentration=True,
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


def test_spell_action_uses_effect_definition_for_damage_and_resource() -> None:
    character = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_1": ResourcePool("spell_slot_1", 1, 1)},
    )
    spell = Spell(
        "guiding_bolt",
        "Guiding Bolt",
        1,
        SpellSchool.EVOCATION,
        "1 action",
        "120 feet",
        "Instantaneous",
        effects=(
            EffectDefinition(
                effect_id="guiding-bolt-damage",
                name="Guiding Bolt",
                effect_kind=EffectKind.DAMAGE,
                target_profile=TargetProfile.ONE_CREATURE,
                resource_cost="spell_slot_1",
                dice="4d6",
            ),
        ),
    )
    app = _app(character, spell)
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "guiding_bolt", "Guiding Bolt")

    message = main_window._activate_spell_button(app, character, button)

    assert "Damage 7 (4d6: rolls=(7,))." in message
    assert "Used level 1 spell slot; 0/1 remain." in message
    assert character.resources["spell_slot_1"].current == 0


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


def test_beacon_of_hope_applies_party_buff_without_damage_message(monkeypatch) -> None:
    caster = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_3": ResourcePool("spell_slot_3", 1, 1)},
    )
    ally = Character("ally", "Ally", HitPoints(10, 10))
    store = FakeCharacterStore((caster, ally))
    app = SimpleNamespace(
        characters=store,
        compendium=FakeCompendium(_beacon_spell()),
        dice=FakeDice(),
    )
    state = main_window.GuiCampaignState(selected_character_id="cleric")
    button = ActionBarButton(
        1,
        ActionBarActionKind.SPELL,
        "beacon_of_hope",
        "Beacon of Hope",
        rank=3,
    )
    monkeypatch.setattr(
        main_window,
        "_choose_beacon_targets",
        lambda *args: ("cleric", "ally"),
    )

    message = main_window._activate_spell_button(app, caster, button, state=state)

    assert "Cleric casts Beacon of Hope on Cleric, Ally." in message
    assert "Hope and Vitality applied while concentration holds." in message
    assert "No damage dice configured" not in message
    assert state.beacon_of_hope_targets == ("cleric", "ally")
    assert state.concentration_character_id == "cleric"
    assert state.concentration_spell_id == "beacon_of_hope"
    assert caster.resources["spell_slot_3"].current == 0
    assert store.saved == [caster]


def test_concentration_spell_persists_active_campaign_state(monkeypatch) -> None:
    caster = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_1": ResourcePool("spell_slot_1", 1, 1)},
    )
    ally = Character("ally", "Ally", HitPoints(10, 10))
    store = FakeCharacterStore((caster, ally))
    campaign_store = FakeCampaignStore(
        Campaign("starter", "Starter", character_ids=("cleric", "ally"))
    )
    app = SimpleNamespace(
        characters=store,
        compendium=FakeCompendium(
            Spell(
                "bless",
                "Bless",
                1,
                SpellSchool.ENCHANTMENT,
                "1 action",
                "30 feet",
                "Concentration, up to 1 minute",
                concentration=True,
            )
        ),
        dice=FakeDice(),
        campaigns=campaign_store,
    )
    state = main_window.GuiCampaignState(
        active_campaign_id="starter",
        selected_character_id="cleric",
    )
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "bless", "Bless")
    monkeypatch.setattr(main_window, "_choose_bless_targets", lambda *args: ("cleric", "ally"))

    message = main_window._activate_spell_button(app, caster, button, state=state)

    assert "Cleric casts Bless on Cleric, Ally." in message
    assert state.active_concentration is not None
    assert state.active_concentration.effect_name == "Bless"
    assert tuple(target.target_id for target in state.active_concentration.targets) == (
        "cleric",
        "ally",
    )
    assert campaign_store.saved[-1].active_concentration == state.active_concentration


def test_new_concentration_spell_clears_beacon_of_hope_targets() -> None:
    caster = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_1": ResourcePool("spell_slot_1", 1, 1)},
    )
    spell = Spell(
        "bless",
        "Bless",
        1,
        SpellSchool.ENCHANTMENT,
        "1 action",
        "30 feet",
        "Concentration, up to 1 minute",
        concentration=True,
    )
    app = _app(caster, spell)
    state = main_window.GuiCampaignState(
        selected_character_id="cleric",
        concentration_character_id="cleric",
        concentration_spell_id="beacon_of_hope",
        beacon_of_hope_targets=("cleric",),
    )
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "bless", "Bless")

    message = main_window._activate_spell_button(app, caster, button, state=state)

    assert "Cleric casts Bless on Cleric." in message
    assert state.beacon_of_hope_targets == ()
    assert state.bless_targets == ("cleric",)
    assert state.concentration_spell_id == "bless"


def test_break_concentration_menu_clears_beacon_of_hope_targets(monkeypatch) -> None:
    character = Character("cleric", "Cleric", HitPoints(20, 20))
    app = _app(character, _beacon_spell())
    state = main_window.GuiCampaignState(
        selected_character_id="cleric",
        concentration_character_id="cleric",
        concentration_spell_id="beacon_of_hope",
        beacon_of_hope_targets=("cleric",),
    )
    window = FakeWindow()
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._break_concentration_from_menu(window, None, app, state)

    assert state.beacon_of_hope_targets == ()
    assert state.concentration_character_id is None
    assert state.concentration_spell_id is None
    assert window.status.message == "Concentration broken: Beacon of Hope."


def test_break_concentration_persists_clear_and_activity(monkeypatch) -> None:
    character = Character("cleric", "Cleric", HitPoints(20, 20))
    campaign_store = FakeCampaignStore(
        Campaign(
            "starter",
            "Starter",
            character_ids=("cleric",),
            active_concentration=ConcentrationState(
                "cleric",
                "beacon_of_hope",
                "Beacon of Hope",
                targets=(
                    TargetReference("cleric", "Cleric", TargetKind.CHARACTER, "cleric"),
                ),
            ),
        )
    )
    app = SimpleNamespace(
        characters=FakeCharacters(character),
        compendium=FakeCompendium(_beacon_spell()),
        dice=FakeDice(),
        campaigns=campaign_store,
    )
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    main_window._load_campaign_concentration(app, state)
    window = FakeWindow()
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._break_concentration_from_menu(window, None, app, state)

    assert state.active_concentration is None
    assert state.beacon_of_hope_targets == ()
    assert campaign_store.saved[-1].active_concentration is None
    assert campaign_store.saved[-1].activity_log[-1].message == (
        "Concentration broken: Beacon of Hope. Removed Beacon of Hope from Cleric."
    )
    assert window._dnd_central.messages == [
        "Concentration broken: Beacon of Hope. Removed Beacon of Hope from Cleric."
    ]


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


def test_cure_wounds_heals_selected_target_and_spends_slot(monkeypatch) -> None:
    caster = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_2": ResourcePool("spell_slot_2", 1, 1)},
    )
    target = Character("ally", "Ally", HitPoints(4, 12))
    store = FakeCharacterStore((caster, target))
    spell = Spell(
        "cure_wounds",
        "Cure Wounds",
        1,
        SpellSchool.EVOCATION,
        "1 action",
        "Touch",
        "Instantaneous",
    )
    app = SimpleNamespace(characters=store, compendium=FakeCompendium(spell), dice=FakeDice(6))
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "cure_wounds", "Cure Wounds", rank=2)
    monkeypatch.setattr(main_window, "_choose_single_party_target", lambda *args: "ally")

    message = main_window._activate_spell_button(
        app,
        caster,
        button,
        state=main_window.GuiCampaignState(),
    )

    assert "Cleric resolves Cure Wounds on Ally [healing]. Total 6." in message
    assert "Healing 2d8: 6" in message
    assert target.hit_points.current == 10
    assert caster.resources["spell_slot_2"].current == 0
    assert target in store.saved


def test_cure_wounds_uses_active_character_target_without_prompt(monkeypatch) -> None:
    caster = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_1": ResourcePool("spell_slot_1", 1, 1)},
    )
    target = Character("ally", "Ally", HitPoints(5, 12))
    store = FakeCharacterStore((caster, target))
    spell = Spell(
        "cure_wounds",
        "Cure Wounds",
        1,
        SpellSchool.EVOCATION,
        "1 action",
        "Touch",
        "Instantaneous",
    )
    app = SimpleNamespace(characters=store, compendium=FakeCompendium(spell), dice=FakeDice(4))
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "cure_wounds", "Cure Wounds")
    state = main_window.GuiCampaignState(
        active_target=TargetReference("ally", "Ally", TargetKind.CHARACTER, "ally"),
    )
    monkeypatch.setattr(
        main_window,
        "_choose_single_party_target",
        lambda *args: (_ for _ in ()).throw(AssertionError("prompt should not open")),
    )

    message = main_window._activate_spell_button(app, caster, button, state=state)

    assert "Cleric resolves Cure Wounds on Ally [healing]. Total 4." in message
    assert target.hit_points.current == 9
    assert caster.resources["spell_slot_1"].current == 0


def test_lesser_restoration_removes_selected_condition(monkeypatch) -> None:
    caster = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        resources={"spell_slot_2": ResourcePool("spell_slot_2", 1, 1)},
    )
    target = Character(
        "ally",
        "Ally",
        HitPoints(10, 10),
        conditions=(Condition(ConditionName.POISONED),),
    )
    store = FakeCharacterStore((caster, target))
    spell = Spell(
        "lesser_restoration",
        "Lesser Restoration",
        2,
        SpellSchool.ABJURATION,
        "1 action",
        "Touch",
        "Instantaneous",
    )
    app = SimpleNamespace(characters=store, compendium=FakeCompendium(spell), dice=FakeDice())
    button = ActionBarButton(
        1,
        ActionBarActionKind.SPELL,
        "lesser_restoration",
        "Lesser Restoration",
        rank=2,
    )
    monkeypatch.setattr(main_window, "_choose_single_party_target", lambda *args: "ally")
    monkeypatch.setattr(main_window, "_choose_lesser_restoration_effect", lambda *args: "Poisoned")

    message = main_window._activate_spell_button(
        app,
        caster,
        button,
        state=main_window.GuiCampaignState(),
    )

    assert "poisoned is ended" in message
    assert target.conditions == ()


def test_thaumaturgy_outputs_selected_effect(monkeypatch) -> None:
    caster = Character("cleric", "Cleric", HitPoints(20, 20))
    spell = Spell(
        "thaumaturgy",
        "Thaumaturgy",
        0,
        SpellSchool.TRANSMUTATION,
        "1 action",
        "30 feet",
        "1 minute",
    )
    app = _app(caster, spell)
    button = ActionBarButton(1, ActionBarActionKind.SPELL, "thaumaturgy", "Thaumaturgy")
    monkeypatch.setattr(
        main_window,
        "_choose_thaumaturgy_effect",
        lambda *args: "A door slams shut.",
    )

    message = main_window._activate_spell_button(
        app,
        caster,
        button,
        state=main_window.GuiCampaignState(),
    )

    assert message == (
        "Cleric casts Thaumaturgy. A door slams shut. "
        "The divine sign lingers for up to 1 minute. No spell slot used."
    )


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


def test_ability_action_applies_damage_to_active_character_target() -> None:
    attacker = Character(
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
    target = Character("goblin", "Goblin", HitPoints(12, 12))
    store = FakeCharacterStore((attacker, target))
    app = SimpleNamespace(
        characters=store,
        compendium=FakeCompendium(_spell()),
        dice=FakeDice(5),
    )
    state = main_window.GuiCampaignState(
        party_leader_character_id="fighter",
        active_target=TargetReference("goblin", "Goblin", TargetKind.CHARACTER, "goblin"),
    )
    button = ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack")

    message = main_window._activate_action_button(app, state, button)

    assert "Fighter resolves Attack with Longsword on Goblin [attack]. Total 5." in message
    assert target.hit_points.current == 7
    assert target in store.saved


def test_ability_action_applies_damage_to_active_monster_target() -> None:
    attacker = Character(
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
    monster = Monster(
        monster_id="goblin",
        name="Goblin",
        armor_class=15,
        hit_points=HitPoints(7, 7),
        abilities=AbilityScores(dexterity=14),
        challenge_rating=Fraction(1, 4),
    )
    participant = EncounterParticipant(
        "goblin",
        "Goblin",
        ParticipantKind.MONSTER,
        "goblin",
        current_hit_points=7,
    )
    encounters = FakeEncounterStore(
        Encounter("ambush", "Ambush", participants=(participant,))
    )
    app = SimpleNamespace(
        characters=FakeCharacterStore((attacker,)),
        compendium=FakeCompendium(_spell(), monster),
        dice=FakeDice(5),
        encounters=encounters,
    )
    state = main_window.GuiCampaignState(
        party_leader_character_id="fighter",
        active_target=TargetReference("goblin", "Goblin", TargetKind.MONSTER, "goblin"),
    )
    button = ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack")

    message = main_window._activate_action_button(app, state, button)

    assert "Fighter resolves Attack with Longsword on Goblin [attack]. Total 5." in message
    assert "HP 2/7" in message
    assert encounters.saved[0].participants[0].current_hit_points == 2


def test_action_activation_handles_empty_selection_and_missing_data() -> None:
    character = Character("fighter", "Fighter", HitPoints(20, 20))
    app = _app(character)
    button = ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack")

    assert main_window._activate_action_button(app, main_window.GuiCampaignState(), None) == (
        "Action slot is empty."
    )
    assert main_window._activate_action_button(
        app,
        main_window.GuiCampaignState(
            selected_character_id=None,
            party_leader_character_id=None,
        ),
        button,
    ) == "Select a party leader or character before using Attack."
    assert main_window._activate_action_button(
        SimpleNamespace(characters=SimpleNamespace(load=_raise_key_error)),
        main_window.GuiCampaignState(
            selected_character_id="missing",
            party_leader_character_id=None,
        ),
        button,
    ) == "Selected character missing could not be loaded."


def test_action_activation_uses_party_leader_before_selected_character() -> None:
    leader = Character(
        "leader",
        "Leader",
        HitPoints(20, 20),
        weapons=(
            Weapon(
                "Mace",
                DamageProfile((DamageComponent("1d6", DamageType.BLUDGEONING),)),
            ),
        ),
    )
    app = _app(leader, total=4)
    button = ActionBarButton(1, ActionBarActionKind.ABILITY, "attack", "Attack")

    message = main_window._activate_action_button(
        app,
        main_window.GuiCampaignState(
            selected_character_id="selected",
            party_leader_character_id="leader",
        ),
        button,
    )

    assert "Leader uses Attack with Mace" in message


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


def test_imported_trait_action_does_not_roll_weapon_damage() -> None:
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(20, 20),
        weapons=(
            Weapon(
                "Handaxe",
                DamageProfile((DamageComponent("1d6+1", DamageType.SLASHING),)),
            ),
        ),
    )
    app = _app(character)
    imported_traits = (
        ("cleric_6", "Cleric 6"),
        ("hill_dwarf", "Hill Dwarf"),
        ("folk_hero", "Folk Hero"),
        ("domain_spells_bless_cure_wounds", "Domain Spells: Bless, Cure Wounds"),
        ("cantrips_light_sacred_flame", "Cantrips: Light, Sacred Flame"),
    )

    for action_id, name in imported_traits:
        button = ActionBarButton(1, ActionBarActionKind.ABILITY, action_id, name)
        assert main_window._activate_ability_button(app, character, button) == (
            f"{name} is character sheet information, not a configured combat action."
        )
    assert app.dice.notations == []


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
    state = main_window.GuiCampaignState(
        selected_character_id="fighter",
        party_leader_character_id="fighter",
    )
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
