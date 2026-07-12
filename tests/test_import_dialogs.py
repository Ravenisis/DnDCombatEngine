import pytest

from dnd_combat_engine.gui.import_dialogs import (
    ask_campaign_name,
    ask_character_id,
    ask_character_url,
    character_import_review_rows,
    choose_character_pdf,
    draft_from_review_rows,
    review_character_import,
)
from dnd_combat_engine.models import (
    AbilityScores,
    Armor,
    CurrencyPurse,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    InventoryItem,
    ItemCategory,
    Weapon,
)
from dnd_combat_engine.models.imports import CharacterImportDraft


class FakeSignal:
    def connect(self, callback) -> None:
        self.callback = callback


class FakeDialog:
    Accepted = 1
    last = None

    class DialogCode:
        Accepted = 1

    def __init__(self, parent) -> None:
        self.parent = parent
        self.title = ""
        self.size = None
        FakeDialog.last = self

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def resize(self, width: int, height: int) -> None:
        self.size = (width, height)

    def accept(self) -> None:
        self.accepted = True

    def reject(self) -> None:
        self.rejected = True

    def exec(self) -> int:
        return self.Accepted


class FakeItem:
    def __init__(self, value: str) -> None:
        self.value = value

    def text(self) -> str:
        return self.value


class FakeTable:
    last = None

    def __init__(self, rows: int, columns: int) -> None:
        self.rows = rows
        self.columns = columns
        self.items = {}
        FakeTable.last = self

    def setHorizontalHeaderLabels(self, labels) -> None:  # noqa: N802
        self.labels = labels

    def setRowCount(self, rows: int) -> None:  # noqa: N802
        self.rows = rows

    def setItem(self, row: int, column: int, item) -> None:  # noqa: N802
        self.items[(row, column)] = item

    def item(self, row: int, column: int):
        return self.items.get((row, column))

    def rowCount(self) -> int:  # noqa: N802
        return self.rows

    def resizeColumnsToContents(self) -> None:  # noqa: N802
        self.resized = True


class FakeLayout:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.widgets = []

    def addWidget(self, widget) -> None:  # noqa: N802
        self.widgets.append(widget)


class FakeButtonBox:
    class StandardButton:
        Ok = 1
        Cancel = 2

    def __init__(self, buttons) -> None:
        self.buttons = buttons
        self.accepted = FakeSignal()
        self.rejected = FakeSignal()


class FakeFileDialog:
    selected = ("sheet.pdf", "")

    @classmethod
    def getOpenFileName(cls, *args):  # noqa: N802
        return cls.selected


class FakeInputDialog:
    selected = ("value", True)

    @classmethod
    def getText(cls, *args):  # noqa: N802
        return cls.selected

    @classmethod
    def getItem(cls, *args):  # noqa: N802
        return cls.selected


class FakeQtWidgets:
    QDialog = FakeDialog
    QDialogButtonBox = FakeButtonBox
    QFileDialog = FakeFileDialog
    QInputDialog = FakeInputDialog
    QTableWidget = FakeTable
    QTableWidgetItem = FakeItem
    QVBoxLayout = FakeLayout


class FakeQt:
    QtWidgets = FakeQtWidgets


def test_import_review_rows_round_trip_editable_character_values() -> None:
    draft = CharacterImportDraft(
        name="Lyra",
        level=3,
        hit_points=HitPoints(7, 12, temporary=2),
        abilities=AbilityScores(dexterity=16),
        character_class="Rogue 3",
        race="Human",
        senses=("Darkvision 60 ft.",),
        initiative_modifier=3,
        heroic_inspiration=True,
        proficiency_bonus=2,
        ability_save_dc=13,
        walking_speed=30,
        spellcasting_ability="Charisma",
        spell_save_dc=13,
        spell_attack_bonus=5,
        saving_throw_modifiers={"dexterity": 5, "wisdom": 2},
        skills=("Stealth", "Perception"),
        inventory=(
            InventoryItem(
                item_id="rope",
                name="Rope",
                category=ItemCategory.ADVENTURING_GEAR,
            ),
        ),
        weapons=(
            Weapon(
                "Rapier",
                DamageProfile((DamageComponent("1d8", DamageType.PIERCING),)),
            ),
        ),
        armor=Armor("Leather", 14),
        features=("Blessed Healer",),
        spells=("Guiding Bolt", "Cure Wounds"),
        saving_throw_proficiencies=("Wisdom", "Charisma"),
        armor_proficiencies=("Light Armor",),
        weapon_proficiencies=("Simple Weapons",),
        tool_proficiencies=("Mason's Tools",),
        languages=("Common", "Dwarvish"),
        damage_resistances=(DamageType.POISON,),
        currency=CurrencyPurse(gp=12, sp=3),
        source="sheet.pdf",
    )
    rows = dict(character_import_review_rows(draft))

    assert "Skills" not in rows
    assert "Saving Throw Proficiencies" not in rows

    rows["Name"] = "Lyra Thorn"
    rows["Inventory"] = "1 x Rope (10 lb); 1 x Clothes, Common (3 lb); Torch"
    rows["Currency"] = "1PP 100GP"
    rows["Weapons"] = "Rapier | 1d8 | piercing; Dagger 1d4 piercing"
    rows["Strength Save Modifier"] = "+1"

    reviewed = draft_from_review_rows(list(rows.items()))

    assert reviewed.name == "Lyra Thorn"
    assert reviewed.level == 3
    assert reviewed.character_class == "Rogue 3"
    assert reviewed.race == "Human"
    assert reviewed.senses == ("Darkvision 60 ft.",)
    assert reviewed.initiative_modifier == 3
    assert reviewed.heroic_inspiration is True
    assert reviewed.proficiency_bonus == 2
    assert reviewed.ability_save_dc == 13
    assert reviewed.walking_speed == 30
    assert reviewed.spellcasting_ability == "Charisma"
    assert reviewed.spell_save_dc == 13
    assert reviewed.spell_attack_bonus == 5
    assert reviewed.saving_throw_modifiers["strength"] == 1
    assert reviewed.saving_throw_modifiers["dexterity"] == 5
    assert reviewed.hit_points.maximum == 12
    assert reviewed.abilities.dexterity == 16
    assert [item.name for item in reviewed.inventory] == ["Rope", "Clothes, Common", "Torch"]
    assert [item.weight for item in reviewed.inventory] == [10.0, 3.0, 0.0]
    assert reviewed.currency.pp == 11
    assert reviewed.currency.gp == 0
    assert [weapon.name for weapon in reviewed.weapons] == ["Rapier", "Dagger"]
    assert reviewed.armor is not None
    assert reviewed.armor.armor_class == 14
    assert reviewed.features == ("Blessed Healer",)
    assert reviewed.spells == ("Guiding Bolt", "Cure Wounds")
    assert reviewed.saving_throw_proficiencies == ()
    assert reviewed.tool_proficiencies == ("Mason's Tools",)
    assert reviewed.damage_resistances == (DamageType.POISON,)


def test_import_review_requires_valid_name_and_numbers() -> None:
    with pytest.raises(ValueError, match="Character name"):
        draft_from_review_rows([("Name", ""), ("Level", "1")])
    with pytest.raises(ValueError, match="Level"):
        draft_from_review_rows([("Name", "Lyra"), ("Level", "zero")])
    with pytest.raises(ValueError, match="Strength"):
        draft_from_review_rows([("Name", "Lyra"), ("Strength", "31")])


def test_file_and_text_import_prompts_return_selected_values() -> None:
    FakeFileDialog.selected = ("C:/tmp/sheet.pdf", "")
    FakeInputDialog.selected = ("https://example.test/sheet.pdf", True)

    assert choose_character_pdf(FakeQt, object()) == "C:/tmp/sheet.pdf"
    assert ask_character_url(FakeQt, object()) == "https://example.test/sheet.pdf"

    FakeInputDialog.selected = ("Storm Coast", True)
    assert ask_campaign_name(FakeQt, object()) == "Storm Coast"

    FakeInputDialog.selected = ("ravenisis", True)
    assert ask_character_id(FakeQt, object(), "Title", "Character:", ("ravenisis",)) == (
        "ravenisis"
    )

    FakeFileDialog.selected = ("", "")
    FakeInputDialog.selected = ("", False)
    assert choose_character_pdf(FakeQt, object()) is None
    assert ask_character_url(FakeQt, object()) is None
    assert ask_campaign_name(FakeQt, object()) is None


def test_review_character_import_accepts_editable_table_values() -> None:
    draft = CharacterImportDraft("Lyra", hit_points=HitPoints(4, 5))

    reviewed = review_character_import(FakeQt, object(), draft)

    assert reviewed is not None
    assert reviewed.name == "Lyra"
    assert FakeDialog.last.title == "Confirm Character Import"
    assert FakeTable.last.labels == ["Name", "Value"]


def test_review_character_import_falls_back_when_dialog_widgets_are_missing() -> None:
    class NoDialogWidgets:
        QFileDialog = None
        QInputDialog = None

    class NoDialogQt:
        QtWidgets = NoDialogWidgets

    draft = CharacterImportDraft("Lyra")

    assert review_character_import(NoDialogQt, object(), draft) == draft
