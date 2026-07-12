from fractions import Fraction
from types import SimpleNamespace

from dnd_combat_engine.gui import (
    campaign,
    campaign_panels,
    inventory,
    spellbook,
    targeting,
    widgets,
)
from dnd_combat_engine.models import (
    AbilityScores,
    Campaign,
    Character,
    Encounter,
    EncounterParticipant,
    HitPoints,
    Monster,
    ParticipantKind,
    TargetKind,
    TargetReference,
)
from dnd_combat_engine.models.damage import DamageComponent, DamageProfile, DamageType
from dnd_combat_engine.models.inventory import InventoryItem, ItemCategory


def test_campaign_state_helpers_choose_leader_and_unique_ids() -> None:
    state = campaign.GuiCampaignState(party_leader_character_id=None, selected_character_id="lyra")

    assert campaign.active_character_id(state) == "lyra"
    assert campaign.active_character_id(campaign.GuiCampaignState()) == "ravenisis"

    app = SimpleNamespace(
        campaigns=SimpleNamespace(list_ids=lambda: ("new_campaign", "new_campaign_2"))
    )
    assert campaign.unique_campaign_id(app, "New Campaign") == "new_campaign_3"


def test_targeting_resolves_character_and_monster_targets() -> None:
    character = Character("lyra", "Lyra", HitPoints(10, 12))
    monster = Monster("goblin", "Goblin", 10, HitPoints(7, 7), character.abilities, Fraction(1, 4))
    participant = EncounterParticipant(
        "goblin",
        "Goblin",
        ParticipantKind.MONSTER,
        "goblin",
        quantity=2,
        current_hit_points=11,
    )
    encounter = Encounter("ambush", "Ambush", participants=(participant,))

    class Characters:
        def load(self, character_id):
            if character_id != "lyra":
                raise KeyError(character_id)
            return character

        def save(self, value):
            self.saved = value

    class Encounters:
        persistence_service = SimpleNamespace(list_encounter_ids=lambda: ("ambush",))

        def load(self, encounter_id):
            if encounter_id != "ambush":
                raise KeyError(encounter_id)
            return encounter

        def save(self, value):
            self.saved = value

    app = SimpleNamespace(
        characters=Characters(),
        compendium=SimpleNamespace(
            load_monster=lambda monster_id: (
                monster if monster_id == "goblin" else (_ for _ in ()).throw(KeyError())
            )
        ),
        encounters=Encounters(),
    )
    character_target = TargetReference("lyra", "Old Name", TargetKind.CHARACTER, "lyra")
    monster_target = TargetReference("goblin", "Goblin", TargetKind.MONSTER, "goblin")
    state = SimpleNamespace(active_target=character_target)

    assert targeting.character_target_reference("lyra").name == "lyra"
    assert targeting.character_target_reference_with_name(app, "lyra").name == "Lyra"
    assert targeting.target_references_for_character_ids(app, ("lyra",))[0].name == "Lyra"
    assert targeting.active_target_for_effect(app, state).name == "Lyra"
    assert targeting.active_character_target_id(app, state) == "lyra"
    assert (
        targeting.apply_damage_to_target(app, character_target, 3) == "Applied 3 damage; HP 7/12."
    )
    assert (
        targeting.active_target_for_effect(app, SimpleNamespace(active_target=monster_target)).name
        == "Goblin"
    )
    assert (
        targeting.active_character_target_id(app, SimpleNamespace(active_target=monster_target))
        is None
    )
    assert targeting.apply_damage_to_target(app, monster_target, 4) == "Applied 4 damage; HP 7/14."
    assert app.encounters.saved.participants[0].current_hit_points == 7
    assert targeting.active_target_for_effect(app, SimpleNamespace(active_target=None)) is None
    assert targeting.active_target_for_effect(app, None) is None


def test_targeting_handles_missing_and_unavailable_targets() -> None:
    missing_app = SimpleNamespace(
        characters=SimpleNamespace(load=lambda _: (_ for _ in ()).throw(KeyError("missing"))),
        compendium=SimpleNamespace(
            load_monster=lambda _: (_ for _ in ()).throw(KeyError("missing"))
        ),
    )
    character_target = TargetReference("missing", "Missing", TargetKind.CHARACTER, "missing")
    monster_target = TargetReference("missing", "Missing", TargetKind.MONSTER, "missing")

    assert (
        targeting.active_target_for_effect(
            missing_app, SimpleNamespace(active_target=character_target)
        )
        is None
    )
    assert (
        targeting.active_target_for_effect(
            missing_app, SimpleNamespace(active_target=monster_target)
        )
        is None
    )
    assert (
        targeting.apply_damage_to_monster_target(
            SimpleNamespace(encounters=SimpleNamespace()), monster_target, 1
        )
        == "Encounter target HP tracking is unavailable."
    )
    assert (
        targeting.apply_damage_to_monster_target(
            SimpleNamespace(
                encounters=SimpleNamespace(
                    persistence_service=SimpleNamespace(list_encounter_ids=lambda: ("missing",)),
                    load=lambda _: (_ for _ in ()).throw(KeyError("missing")),
                )
            ),
            monster_target,
            1,
        )
        == "Encounter target could not be found."
    )


def test_campaign_panel_target_helpers_cover_missing_and_hp_paths() -> None:
    character = Character("lyra", "Lyra", HitPoints(8, 10))
    monster = Monster("goblin", "Goblin", 10, HitPoints(7, 7), character.abilities, Fraction(1, 4))
    target_character = TargetReference("lyra", "Lyra", TargetKind.CHARACTER, "lyra")
    target_monster = TargetReference("goblin", "Goblin", TargetKind.MONSTER, "goblin")
    encounter = Encounter(
        "ambush",
        "Ambush",
        participants=(EncounterParticipant("goblin", "Goblin", ParticipantKind.MONSTER, "goblin"),),
    )
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda _: Campaign(
                "camp",
                "Camp",
                character_ids=("lyra",),
                encounter_ids=("ambush",),
            )
        ),
        characters=SimpleNamespace(
            load=lambda identifier: (
                character if identifier == "lyra" else (_ for _ in ()).throw(KeyError())
            )
        ),
        encounters=SimpleNamespace(
            load=lambda _: encounter,
            persistence_service=SimpleNamespace(list_encounter_ids=lambda: ("ambush",)),
        ),
        compendium=SimpleNamespace(
            load_monster=lambda identifier: (
                monster if identifier == "goblin" else (_ for _ in ()).throw(KeyError())
            )
        ),
    )

    assert campaign_panels._target_panel_references(app, None) == ()
    targets = campaign_panels._target_panel_references(app, "camp")
    assert tuple(target.kind for target in targets) == (TargetKind.CHARACTER, TargetKind.MONSTER)
    assert "HP 8/10 THP 0" in campaign_panels._target_button_text(app, target_character)
    assert "HP 7/7" in campaign_panels._target_button_text(app, target_monster)
    assert (
        campaign_panels._target_button_text(
            app, TargetReference("x", "X", TargetKind.CHARACTER, "x")
        )
        == "X\nMissing character"
    )
    assert (
        campaign_panels._target_button_text(app, TargetReference("x", "X", TargetKind.MONSTER, "x"))
        == "X\nMissing monster"
    )
    assert campaign_panels._monster_target_current_hp(app, target_monster, 7) == 7

    unavailable = SimpleNamespace(encounters=SimpleNamespace())
    assert campaign_panels._monster_target_current_hp(unavailable, target_monster, 7) == 7
    assert (
        campaign_panels._target_panel_references(
            SimpleNamespace(
                campaigns=SimpleNamespace(load=lambda _: (_ for _ in ()).throw(KeyError()))
            ),
            "camp",
        )
        == ()
    )
    assert (
        campaign_panels._campaign_character_selector(
            SimpleNamespace(QtWidgets=SimpleNamespace(QLineEdit=lambda value: value)), ()
        )
        == ""
    )
    assert campaign_panels._selector_text(SimpleNamespace(text=lambda: " Lyra ")) == "Lyra"


def test_spellbook_helpers_cover_tab_and_character_paths() -> None:
    character = Character(
        "lyra", "Lyra", HitPoints(10, 10), features=("Channel Divinity: Turn Undead",)
    )
    app = SimpleNamespace(
        characters=SimpleNamespace(
            load=lambda identifier: (
                character if identifier == "lyra" else (_ for _ in ()).throw(KeyError())
            )
        )
    )
    assert spellbook._attack_names_for_character(app, None) == ()
    assert spellbook._attack_names_for_character(app, "missing") == ()
    assert spellbook._attack_names_for_character(app, "lyra") == ("Unarmed Strike",)
    assert spellbook._actionable_ability_names_for_tab(app, None) == ()
    assert spellbook._actionable_ability_names_for_tab(app, "missing") == ()
    assert spellbook._actionable_ability_names_for_tab(app, "lyra") == (
        "Basic Attack",
        "Channel Divinity: Turn Undead",
    )
    assert spellbook._is_channel_divinity_name("Channel Divinity: Turn Undead")
    assert not spellbook._is_channel_divinity_name("Rage")

    class Layout:
        def __init__(self, parent):
            parent.layout = self
            self.widgets = []

        def addWidget(self, widget):
            self.widgets.append(widget)

        def addStretch(self, value):
            self.stretch = value

    class Widget:
        pass

    class Widgets:
        QWidget = Widget
        QVBoxLayout = Layout

        class QLabel:
            def __init__(self, text):
                self.text = text

    qt = SimpleNamespace(QtWidgets=Widgets)
    tabs = spellbook._spellbook_tabs(qt)
    tab = spellbook._spellbook_tab(qt)
    spellbook._add_spellbook_tab(tabs, tab, "Spells")
    spellbook._spellbook_tab_finish(qt, tab)
    assert tab._dnd_spellbook_tab_count == 0
    spellbook._spellbook_tab_add_widget(tab, object())
    spellbook._spellbook_tab_finish(qt, tab)
    assert tab._dnd_spellbook_tab_count == 1


def test_inventory_widget_delegates_to_inventory_helpers(monkeypatch) -> None:
    character = Character("lyra", "Lyra", HitPoints(10, 10))
    app = SimpleNamespace(characters=SimpleNamespace(load=lambda _: character))

    class Widget:
        pass

    class Layout:
        def __init__(self, parent):
            parent.layout = self
            self.widgets = []

        def addWidget(self, widget):
            self.widgets.append(widget)

        def addStretch(self, value):
            self.stretch = value

    qt = SimpleNamespace(QtWidgets=SimpleNamespace(QWidget=Widget, QVBoxLayout=Layout))
    from dnd_combat_engine.gui import widgets

    monkeypatch.setattr(widgets, "_inventory_header", lambda *args: "header")
    monkeypatch.setattr(widgets, "_inventory_sections", lambda _: ())

    widget = inventory.InventoryWidget.create(app, qt, "lyra")

    assert widget.layout.widgets == ["header"]


def test_widget_data_helpers_cover_inventory_action_and_save_paths() -> None:
    item = InventoryItem(
        "potion_of_healing_greater",
        "Potion of Healing (Greater)",
        quantity=2,
        weight=0.5,
        category=ItemCategory.CONSUMABLE,
        tags=("potion", "healing"),
        notes="Regain hit points.",
    )
    assert widgets._inventory_quantity_text(item) == "2"
    assert widgets._inventory_quantity_text(item.with_quantity(1)) == ""
    assert widgets._sell_price_cp(item) == 25_000
    assert (
        widgets._inventory_sections((InventoryItem("backpack", "Backpack"), item))[1][1][0].name
        == item.name
    )
    assert widgets._is_container_item(InventoryItem("pouch", "Pouch"))
    assert not widgets._is_container_item(InventoryItem("rope", "Rope"))
    assert "potion" in widgets._inventory_icon_candidates(item)
    assert (
        widgets._damage_profile_text(DamageProfile((DamageComponent("1d4", DamageType.RADIANT),)))
        == "1d4 radiant"
    )
    assert widgets._wrap_tooltip_text("short text", width=4) == "shor\nt\ntext"
    assert widgets._currency_price_text(1_234) == "1PP 2GP 3SP 4CP"
    assert widgets._proficiency_bonus(1) == 2
    assert widgets._proficiency_bonus(9) == 4

    character = Character(
        "lyra",
        "Lyra",
        HitPoints(10, 10),
        abilities=AbilityScores(wisdom=14),
        saving_throw_proficiencies=("wisdom",),
    )
    assert widgets._saving_throw_modifier(character, "wisdom") == 4
    assert widgets._saving_throw_modifier(character, "strength") == 0
    assert widgets._trigger_saving_throw(lambda ability: (ability, False), "wisdom", True) == (
        "wisdom",
        False,
    )
    assert (
        widgets._trigger_saving_throw(
            lambda ability, advantage: (ability, advantage), "wisdom", True
        )
        == ("wisdom", True)
    )
    assert widgets._initiative_text("missing", {}) == "Initiative: - | Position: -"
    assert widgets._parse_initiative_value("-12") == -12
    assert widgets._parse_initiative_value("1234") is None
    assert widgets._action_id("Channel Divinity: Turn Undead") == "channel_divinity:_turn_undead"


def test_widget_context_helpers_cover_menu_and_action_button_paths() -> None:
    class Signal:
        def __init__(self):
            self.callback = None

        def connect(self, callback):
            self.callback = callback

    class Action:
        def __init__(self, label):
            self.label = label
            self.triggered = Signal()

        def setEnabled(self, value):
            self.enabled = value

    class Menu:
        def __init__(self, parent=None):
            self.actions = []

        def addAction(self, label):
            action = Action(label)
            self.actions.append(action)
            return action

        def exec(self, position):
            self.position = position

    class MouseButton:
        RightButton = 2
        LeftButton = 1

    class KeyboardModifier:
        ShiftModifier = 4

    class QtWidgets:
        QMenu = Menu

    qt = SimpleNamespace(
        QtWidgets=QtWidgets,
        QtCore=SimpleNamespace(
            Qt=SimpleNamespace(MouseButton=MouseButton, KeyboardModifier=KeyboardModifier)
        ),
    )
    calls = []

    class Event:
        def globalPos(self):
            return "global"

        def pos(self):
            return "local"

    button = SimpleNamespace(mapToGlobal=lambda value: f"mapped:{value}")
    item = InventoryItem("potion", "Potion", category=ItemCategory.CONSUMABLE)
    widgets._show_inventory_item_menu(
        qt,
        button,
        item,
        lambda item_id: calls.append(("consume", item_id)) or 1,
        lambda item_id: calls.append(("sell", item_id)) or 1,
        Event(),
    )
    assert calls == []
    assert widgets._is_right_click(qt, SimpleNamespace(button=lambda: 2)) is True
    assert widgets._is_right_click(qt, SimpleNamespace(button=lambda: 1)) is False

    class BaseButton:
        def __init__(self, text):
            self.text = text
            self.enabled = True

        def setText(self, text):
            self.text = text

        def setEnabled(self, enabled):
            self.enabled = enabled

        def mousePressEvent(self, event):
            self.base_called = True

    qt.QtWidgets.QPushButton = BaseButton
    button_class = widgets._inventory_button_class(
        qt,
        item,
        lambda item_id: calls.append(("consume", item_id)) or 0,
        lambda item_id: calls.append(("sell", item_id)) or 0,
    )
    button_instance = button_class("2")
    button_instance.mousePressEvent(SimpleNamespace(button=lambda: 1, modifiers=lambda: 0))
    assert button_instance.base_called is True

    assert widgets._set_inventory_button_remaining(button_instance, 0) is None
    assert button_instance.enabled is False
    assert button_instance.text == ""


def test_main_window_action_helpers_cover_data_driven_roll_paths() -> None:
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.models import (
        ActionBarActionKind,
        ActionBarButton,
        DamageComponent,
        DamageProfile,
        DamageType,
        EffectDefinition,
        EffectKind,
        Spell,
        SpellSchool,
        TargetProfile,
        Weapon,
    )

    assert main_window._dice_notation_from_action("dice.roll_d20") == "1d20"
    assert main_window._dice_notation_from_action("dice.roll_d3") is None
    assert main_window._is_spell_slot_resource("spell_slot_2")
    assert not main_window._is_spell_slot_resource("hit_dice")
    for name, notation in (
        ("Potion of Healing", "2d4+2"),
        ("Potion of Healing (Greater)", "4d4+4"),
        ("Potion of Healing (Superior)", "8d4+8"),
        ("Potion of Healing (Supreme)", "10d4+20"),
    ):
        assert main_window._healing_potion_notation(InventoryItem(name.lower(), name)) == notation
    assert main_window._healing_potion_notation(InventoryItem("rope", "Rope")) is None

    weapon = Weapon(
        "Handaxe",
        DamageProfile((DamageComponent("1d6", DamageType.SLASHING),)),
    )
    character = Character(
        "lyra",
        "Lyra",
        HitPoints(10, 10),
        level=5,
        character_class="Cleric",
        abilities=AbilityScores(strength=14, wisdom=16),
        weapons=(weapon,),
    )
    spell = Spell("bless", "Bless", 1, SpellSchool.ENCHANTMENT, "1 action", "30 feet", "1 minute")
    dice = SimpleNamespace(
        roll=lambda notation: SimpleNamespace(notation=notation, total=5, rolls=(5,))
    )
    app = SimpleNamespace(
        dice=dice,
        compendium=SimpleNamespace(load_spell=lambda _: spell),
    )
    spell_button = ActionBarButton(1, ActionBarActionKind.SPELL, "bless", "Bless", 1)
    attack_button = ActionBarButton(1, ActionBarActionKind.ABILITY, "handaxe", "Handaxe", 1)
    assert main_window._character_spellcasting_ability(character) == "wisdom"
    assert main_window._character_spellcasting_ability(
        Character("wizard", "Wizard", HitPoints(1, 1), character_class="Wizard")
    ) == "intelligence"
    assert main_window._character_spellcasting_ability(
        Character("bard", "Bard", HitPoints(1, 1), character_class="Bard")
    ) == "charisma"
    assert main_window._ability_for_action_name("Dexterity Check", character) == "dexterity"
    assert main_window._ability_for_action_name("Channel Divinity", character) == "wisdom"
    assert main_window._ability_for_action_name("Unarmed Strike", character) == "strength"
    assert main_window._ability_uses_weapon_damage(character, attack_button)
    assert main_window._weapon_for_button(character, attack_button) == weapon
    assert main_window._weapon_for_button(
        Character("empty", "Empty", HitPoints(1, 1)), attack_button
    ) is None
    assert main_window._action_bar_check_modifier(app, character, spell_button) == (
        6,
        "spell attack",
    )
    assert main_window._action_bar_check_modifier(app, character, attack_button) == (5, "attack")
    assert main_window._roll_damage_profile(app, weapon.damage)[1] == 5
    assert main_window._critical_damage_notation("4d6") == "8d6"
    assert main_window._critical_damage_notation("2d8+1") == "4d8+1"
    assert main_window._critical_damage_notation("1d8+spellcasting_modifier") == (
        "1d8+spellcasting_modifier"
    )
    effect = EffectDefinition(
        effect_id="guiding-bolt-damage",
        name="Guiding Bolt",
        effect_kind=EffectKind.DAMAGE,
        target_profile=TargetProfile.ONE_CREATURE,
        dice="4d6",
    )
    message, total = main_window._roll_spell_effect_damage(app, None, effect, critical=True)
    assert "8d6" in message
    assert total == 5
    assert main_window._roll_damage_profile(app, None) == ("No damage dice configured.", 0)
    assert main_window._action_identifier("Channel Divinity: Turn Undead") == (
        "channel_divinity_turn_undead"
    )
    assert main_window._currency_change_text(1_234) == "1PP 2GP 3SP 4CP"
    assert main_window._default_inventory_item_price_cp(
        InventoryItem("potion_of_greater_healing", "Potion")
    ) == 50_000
