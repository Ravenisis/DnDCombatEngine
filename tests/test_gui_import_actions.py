from types import SimpleNamespace

from dnd_combat_engine.gui import main_window
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.models import (
    BetaBugReport,
    Campaign,
    Character,
    HitPoints,
    ResourcePool,
    Spell,
    SpellSchool,
)
from dnd_combat_engine.models.imports import CharacterImportDraft


class FakeStatusBar:
    def __init__(self) -> None:
        self.message = ""

    def showMessage(self, message) -> None:
        self.message = message


class FakeWindow:
    def __init__(self) -> None:
        self.status = FakeStatusBar()
        self.closed = False

    def statusBar(self):
        return self.status

    def close(self) -> None:
        self.closed = True


class FakeWorkspace:
    def __init__(self) -> None:
        self.messages = []

    def append(self, value) -> None:
        self.messages.append(value)


class FakeMessageBox:
    information_calls: list[tuple[object, str, str]] = []
    warning_calls: list[tuple[object, str, str]] = []

    @classmethod
    def information(cls, parent, title, message) -> None:
        cls.information_calls.append((parent, title, message))

    @classmethod
    def warning(cls, parent, title, message) -> None:
        cls.warning_calls.append((parent, title, message))


class FakeQtWidgets:
    QMessageBox = FakeMessageBox


class FakeQt:
    QtWidgets = FakeQtWidgets


class FakeSignal:
    def connect(self, callback) -> None:
        self.callback = callback


class FakeDialog:
    last = None

    def __init__(self, parent) -> None:
        self.parent = parent
        self.title = ""
        self.size = None
        self.shown = False
        FakeDialog.last = self

    def setWindowTitle(self, title) -> None:  # noqa: N802
        self.title = title

    def resize(self, width, height) -> None:
        self.size = (width, height)

    def show(self) -> None:
        self.shown = True


class FakeWidget:
    def __init__(self, *args) -> None:
        self.args = args

    def setReadOnly(self, value) -> None:  # noqa: N802
        self.read_only = value

    def append(self, value) -> None:
        self.appended = value


class FakeLayout:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.widgets = []

    def addWidget(self, widget) -> None:  # noqa: N802
        self.widgets.append(widget)


class FakeButton(FakeWidget):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.clicked = FakeSignal()


class FakePopupQtWidgets(FakeQtWidgets):
    QDialog = FakeDialog
    QLabel = FakeWidget
    QPushButton = FakeButton
    QTextEdit = FakeWidget
    QVBoxLayout = FakeLayout
    QWidget = FakeWidget


class FakePopupQt:
    QtWidgets = FakePopupQtWidgets


def _import_result() -> SimpleNamespace:
    character = Character("lyra", "Lyra", HitPoints(10, 10))
    campaign = Campaign("starter", "Starter", character_ids=("lyra",))
    return SimpleNamespace(character=character, campaign=campaign)


def test_dice_menu_rolls_standard_die_and_ctrl_r_repeats_previous() -> None:
    class FakeDice:
        def __init__(self) -> None:
            self.notations = []

        def roll(self, notation: str):
            self.notations.append(notation)
            return SimpleNamespace(total=len(self.notations), rolls=(len(self.notations),))

    window = FakeWindow()
    window._dnd_central = FakeWorkspace()
    state = main_window.GuiCampaignState()
    app = SimpleNamespace(dice=FakeDice())

    main_window._run_menu_action(window, FakeQt, app, state, "dice.roll_d8")
    main_window._run_menu_action(window, FakeQt, app, state, "dice.repeat_last")

    assert app.dice.notations == ["1d8", "1d8"]
    assert state.last_dice_notation == "1d8"
    assert window._dnd_central.messages == [
        "d8 roll: 1 rolls=(1,)",
        "d8 roll: 2 rolls=(2,)",
    ]
    assert window.status.message == "d8 roll: 2 rolls=(2,)"


def test_pdf_menu_action_runs_import_and_reports_status(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(
        active_campaign_id="starter",
        selected_character_id=None,
        party_leader_character_id=None,
    )
    app = SimpleNamespace(
        character_imports=SimpleNamespace(
            preview_pdf=lambda path: CharacterImportDraft("Lyra", hit_points=HitPoints(10, 10)),
            import_draft_to_campaign=lambda draft, campaign_id: _import_result(),
        )
    )
    FakeMessageBox.information_calls = []
    monkeypatch.setattr(main_window, "choose_character_pdf", lambda qt, parent: "sheet.pdf")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.import_pdf")

    assert window.status.message == "Imported Lyra as lyra and added them to Starter."
    assert state.selected_character_id == "lyra"
    assert state.party_leader_character_id == "lyra"
    assert FakeMessageBox.information_calls[-1][1] == "Character Imported"


def test_url_menu_action_runs_import_and_reports_errors(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter", selected_character_id=None)
    FakeMessageBox.warning_calls = []
    monkeypatch.setattr(main_window, "ask_character_url", lambda qt, parent: "https://example.test")

    def fail_import(url, campaign_id):
        raise ValueError("could not import")

    app = SimpleNamespace(character_imports=SimpleNamespace(import_url_to_campaign=fail_import))
    main_window._run_menu_action(window, FakeQt, app, state, "campaign.import_url")

    assert window.status.message == "could not import"
    assert FakeMessageBox.warning_calls[-1][1] == "Import Failed"


def test_report_bug_menu_writes_beta_report(monkeypatch, tmp_path) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState()
    report_file = tmp_path / "BETA_TESTER_REPORTS.md"
    report = BetaBugReport("Crash on launch", "The app closes immediately.")
    FakeMessageBox.information_calls = []

    def submit_bug_report(submitted):
        report_file.write_text(submitted.summary, encoding="utf-8")
        return report_file

    app = SimpleNamespace(beta_reports=SimpleNamespace(submit_bug_report=submit_bug_report))
    monkeypatch.setattr(main_window, "_ask_bug_report", lambda qt, parent: report)

    main_window._run_menu_action(window, FakeQt, app, state, "help.report_bug")

    assert report_file.read_text(encoding="utf-8") == "Crash on launch"
    assert FakeMessageBox.information_calls[-1][1] == "Bug Report Submitted"
    assert window.status.message == f"Submitted bug report to {report_file}."


def test_report_bug_menu_handles_cancel(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState()
    monkeypatch.setattr(main_window, "_ask_bug_report", lambda qt, parent: None)

    main_window._run_menu_action(window, FakeQt, object(), state, "help.report_bug")

    assert window.status.message == "Bug report canceled."


def test_report_bug_dialog_requires_summary_before_accepting() -> None:
    class Dialog:
        class DialogCode:
            Accepted = 1

        def __init__(self, parent) -> None:
            self.accepted = False
            self.rejected = False

        def setWindowTitle(self, title) -> None:  # noqa: N802
            self.title = title

        def resize(self, width, height) -> None:
            self.size = (width, height)

        def accept(self) -> None:
            self.accepted = True

        def reject(self) -> None:
            self.rejected = True

        def exec(self) -> int:
            ButtonBox.last.accepted.callback()
            return self.DialogCode.Accepted if self.accepted else 0

    class LineEdit:
        def text(self) -> str:
            return ""

    class TextEdit:
        def toPlainText(self) -> str:  # noqa: N802
            return "The report description."

    class ComboBox:
        def __init__(self) -> None:
            self.items = []

        def addItem(self, value) -> None:  # noqa: N802
            self.items.append(value)

        def currentText(self) -> str:  # noqa: N802
            return self.items[0]

    class Layout:
        def __init__(self, parent=None) -> None:
            self.parent = parent

        def addWidget(self, widget) -> None:  # noqa: N802
            self.widget = widget

    class ButtonBox:
        class StandardButton:
            Ok = 1
            Cancel = 2

        last = None

        def __init__(self, buttons) -> None:
            self.buttons = buttons
            self.accepted = FakeSignal()
            self.rejected = FakeSignal()
            ButtonBox.last = self

    class MessageBox:
        warning_calls = []

        @classmethod
        def warning(cls, parent, title, message) -> None:
            cls.warning_calls.append((parent, title, message))

    class QtWidgets:
        QComboBox = ComboBox
        QDialog = Dialog
        QDialogButtonBox = ButtonBox
        QHBoxLayout = Layout
        QLabel = FakeWidget
        QLineEdit = LineEdit
        QMessageBox = MessageBox
        QTextEdit = TextEdit
        QVBoxLayout = Layout
        QWidget = FakeWidget

    report = main_window._ask_bug_report(SimpleNamespace(QtWidgets=QtWidgets), object())

    assert report is None
    assert MessageBox.warning_calls[-1][1:] == ("Report Bug", "Summary is required.")


def test_close_campaign_clears_active_state(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(
        active_campaign_id="starter",
        selected_character_id="vale",
        party_leader_character_id="vale",
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, object(), state, "campaign.close")

    assert state.active_campaign_id is None
    assert state.selected_character_id is None
    assert state.party_leader_character_id is None
    assert window.status.message == "Campaign closed."


def test_begin_new_campaign_creates_and_opens_campaign(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id=None, selected_character_id=None)
    saved_campaigns = []
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            list_ids=lambda: ("starter",),
            save=saved_campaigns.append,
        )
    )
    monkeypatch.setattr(main_window, "ask_campaign_name", lambda qt, parent: "Storm Coast")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.new")

    assert saved_campaigns[-1] == Campaign("storm_coast", "Storm Coast")
    assert state.active_campaign_id == "storm_coast"
    assert state.selected_character_id is None
    assert state.party_leader_character_id is None
    assert window.status.message == "Created Storm Coast."


def test_add_party_member_menu_adds_existing_character(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(
        active_campaign_id="starter",
        selected_character_id=None,
        party_leader_character_id=None,
    )
    saved_campaigns = []
    character = Character("bran", "Bran", HitPoints(12, 12))
    app = SimpleNamespace(
        characters=SimpleNamespace(
            list_ids=lambda: ["bran"],
            load=lambda character_id: character,
        ),
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(campaign_id, "Starter"),
            add_character=lambda campaign, character_id: campaign.with_character(character_id),
            save=saved_campaigns.append,
        ),
    )
    monkeypatch.setattr(main_window, "ask_character_id", lambda *args: "bran")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.add_party_member")

    assert saved_campaigns[-1].character_ids == ("bran",)
    assert state.selected_character_id == "bran"
    assert state.party_leader_character_id == "bran"
    assert window.status.message == "Added Bran to party."


def test_add_party_member_menu_requires_open_campaign() -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id=None)
    FakeMessageBox.warning_calls = []

    main_window._run_menu_action(window, FakeQt, object(), state, "campaign.add_party_member")

    assert window.status.message == "Open or create a campaign first."
    assert FakeMessageBox.warning_calls[-1][1] == "Add Failed"


def test_add_party_member_menu_handles_cancel(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    app = SimpleNamespace(characters=SimpleNamespace(list_ids=lambda: ["vale"]))
    monkeypatch.setattr(main_window, "ask_character_id", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.add_party_member")

    assert window.status.message == "Add party member canceled."


def test_set_party_leader_menu_updates_active_spellbook_context(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(
        active_campaign_id="starter",
        selected_character_id="vale",
        party_leader_character_id="vale",
    )
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(
                campaign_id,
                "Starter",
                character_ids=("vale", "bran"),
            )
        )
    )
    monkeypatch.setattr(main_window, "ask_character_id", lambda *args: "bran")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.set_party_leader")

    assert state.party_leader_character_id == "bran"
    assert state.selected_character_id == "bran"
    assert window.status.message == "Set bran as party leader."


def test_set_party_leader_menu_requires_party_members() -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    app = SimpleNamespace(
        campaigns=SimpleNamespace(load=lambda campaign_id: Campaign(campaign_id, "Starter"))
    )
    FakeMessageBox.warning_calls = []

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.set_party_leader")

    assert window.status.message == "The active campaign has no party members."
    assert FakeMessageBox.warning_calls[-1][1] == "Leader Failed"


def test_set_party_leader_menu_rejects_non_party_member(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(
                campaign_id,
                "Starter",
                character_ids=("vale",),
            )
        )
    )
    FakeMessageBox.warning_calls = []
    monkeypatch.setattr(main_window, "ask_character_id", lambda *args: "bran")

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.set_party_leader")

    assert window.status.message == "bran is not in the active party."
    assert FakeMessageBox.warning_calls[-1][1] == "Leader Failed"


def test_long_rest_heals_party_and_restores_spell_slots(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(3, 20, temporary=4),
        resources={
            "spell_slot_1": ResourcePool("spell_slot_1", 0, 4),
            "channel_divinity": ResourcePool("channel_divinity", 0, 1),
        },
    )
    saved_characters = []
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(
                campaign_id,
                "Starter",
                character_ids=("ravenisis",),
            )
        ),
        characters=SimpleNamespace(
            load=lambda character_id: character,
            save=saved_characters.append,
        ),
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.long_rest")

    assert character.hit_points.current == 20
    assert character.hit_points.temporary == 0
    assert character.resources["spell_slot_1"].current == 4
    assert character.resources["channel_divinity"].current == 1
    assert saved_characters == [character]
    assert window.status.message == (
        "Long rest completed for 1 party member. Hit points and spell slots restored."
    )


def test_campaign_activity_is_recorded_from_gui_action() -> None:
    campaign = Campaign("starter", "Starter")
    saved = []
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: campaign,
            save=saved.append,
        )
    )
    state = main_window.GuiCampaignState(active_campaign_id="starter")

    main_window._record_campaign_activity(app, state, "Money changed.", "currency")

    assert saved[0].activity_log[0].message == "Money changed."
    assert saved[0].activity_log[0].category == "currency"


def test_long_rest_restores_imported_spell_slots(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    draft = CharacterImportDraft(
        "Ravenisis",
        level=6,
        hit_points=HitPoints(3, 20),
        resources={
            "spell_slot_1": ResourcePool("spell_slot_1", 0, 4),
            "spell_slot_2": ResourcePool("spell_slot_2", 0, 3),
            "spell_slot_3": ResourcePool("spell_slot_3", 0, 3),
        },
    )
    character = draft.to_character("ravenisis")
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(
                campaign_id,
                "Starter",
                character_ids=("ravenisis",),
            )
        ),
        characters=SimpleNamespace(
            load=lambda character_id: character,
            save=lambda saved: None,
        ),
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.long_rest")

    assert character.resources["spell_slot_1"].current == 4
    assert character.resources["spell_slot_2"].current == 3
    assert character.resources["spell_slot_3"].current == 3


def test_long_rest_repairs_missing_spell_slots_for_legacy_import(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(3, 20, temporary=4),
        level=6,
        features=(
            "Cleric 6",
            "Cantrips: Light, Sacred Flame, Thaumaturgy",
            "Domain Spells: Bless, Cure Wounds, Revivify",
        ),
    )
    saved_characters = []
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(
                campaign_id,
                "Starter",
                character_ids=("ravenisis",),
            )
        ),
        characters=SimpleNamespace(
            load=lambda character_id: character,
            save=saved_characters.append,
        ),
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.long_rest")

    assert character.resources["spell_slot_1"].current == 4
    assert character.resources["spell_slot_2"].current == 3
    assert character.resources["spell_slot_3"].current == 3
    assert saved_characters == [character]


def test_short_rest_heals_and_keeps_spell_slots_spent(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(3, 20, temporary=2),
        resources={
            "spell_slot_1": ResourcePool("spell_slot_1", 0, 4),
            "second_wind": ResourcePool("second_wind", 0, 1),
        },
    )
    saved_characters = []
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(
                campaign_id,
                "Starter",
                character_ids=("ravenisis",),
            )
        ),
        characters=SimpleNamespace(
            load=lambda character_id: character,
            save=saved_characters.append,
        ),
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.short_rest")

    assert character.hit_points.current == 13
    assert character.hit_points.temporary == 2
    assert character.resources["spell_slot_1"].current == 0
    assert character.resources["second_wind"].current == 1
    assert saved_characters == [character]
    assert window.status.message == (
        "Short rest completed for 1 party member. "
        "Partial hit points and short-rest resources restored."
    )


def test_rest_menu_requires_open_campaign() -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id=None)
    FakeMessageBox.warning_calls = []

    main_window._run_menu_action(window, FakeQt, object(), state, "campaign.long_rest")

    assert window.status.message == "Open or create a campaign first."
    assert FakeMessageBox.warning_calls[-1][1] == "Rest Failed"


def test_rest_menu_reports_missing_campaign() -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="missing")
    FakeMessageBox.warning_calls = []

    def missing_campaign(campaign_id):
        raise KeyError(campaign_id)

    app = SimpleNamespace(campaigns=SimpleNamespace(load=missing_campaign))

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.long_rest")

    assert window.status.message == "'missing'"
    assert FakeMessageBox.warning_calls[-1][1] == "Rest Failed"


def test_rest_menu_skips_missing_party_members(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter")
    saved_characters = []

    def load_character(character_id):
        raise KeyError(character_id)

    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(campaign_id, "Starter", character_ids=("missing",))
        ),
        characters=SimpleNamespace(load=load_character, save=saved_characters.append),
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.short_rest")

    assert saved_characters == []
    assert window.status.message == (
        "Short rest completed for 0 party members. "
        "Partial hit points and short-rest resources restored."
    )


def test_character_spellbook_menu_opens_party_leader_popup() -> None:
    window = FakeWindow()
    window._dnd_action_bar_session = ActionBarSession()
    state = main_window.GuiCampaignState(
        selected_character_id="vale",
        party_leader_character_id="ravenisis",
    )
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(20, 20),
        features=("Domain Spells: Bless",),
    )
    spell = Spell(
        "bless",
        "Bless",
        1,
        SpellSchool.ENCHANTMENT,
        "1 action",
        "30 feet",
        "1 minute",
    )
    app = SimpleNamespace(
        characters=SimpleNamespace(load=lambda character_id: character),
        compendium=SimpleNamespace(
            persistence_service=SimpleNamespace(list_spell_ids=lambda: ["bless"]),
            load_spell=lambda spell_id: spell,
        ),
    )

    main_window._run_menu_action(window, FakePopupQt, app, state, "character.spellbook")

    assert FakeDialog.last.title == "Ravenisis Spellbook"
    assert FakeDialog.last.size == (360, 520)
    assert FakeDialog.last.shown is True
    assert window._dnd_popups == [FakeDialog.last]
    assert window.status.message == "Opened Ravenisis spellbook."


def test_character_spellbook_menu_reports_missing_action_bar() -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(party_leader_character_id="ravenisis")
    FakeMessageBox.warning_calls = []

    main_window._run_menu_action(window, FakeQt, object(), state, "character.spellbook")

    assert window.status.message == "Action bar is not ready."
    assert FakeMessageBox.warning_calls[-1][1] == "Spellbook Failed"


def test_character_spellbook_menu_requires_party_leader() -> None:
    window = FakeWindow()
    window._dnd_action_bar_session = ActionBarSession()
    state = main_window.GuiCampaignState(
        selected_character_id=None,
        party_leader_character_id=None,
    )
    FakeMessageBox.warning_calls = []

    main_window._run_menu_action(window, FakeQt, object(), state, "character.spellbook")

    assert window.status.message == "Set a party leader before opening the spellbook."
    assert FakeMessageBox.warning_calls[-1][1] == "Spellbook Failed"


def test_character_spellbook_menu_reports_missing_party_leader_data() -> None:
    window = FakeWindow()
    window._dnd_action_bar_session = ActionBarSession()
    state = main_window.GuiCampaignState(party_leader_character_id="missing")

    def missing_character(character_id):
        raise KeyError(character_id)

    app = SimpleNamespace(characters=SimpleNamespace(load=missing_character))
    FakeMessageBox.warning_calls = []

    main_window._run_menu_action(window, FakeQt, app, state, "character.spellbook")

    assert window.status.message == "Party leader missing could not be loaded."
    assert FakeMessageBox.warning_calls[-1][1] == "Spellbook Failed"


def test_replace_party_member_sheet_saves_over_existing_character(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter", selected_character_id="vale")
    saved_characters = []
    app = SimpleNamespace(
        character_imports=SimpleNamespace(
            preview_pdf=lambda path: CharacterImportDraft("Ravenisis", hit_points=HitPoints(8, 8))
        ),
        characters=SimpleNamespace(save=saved_characters.append),
    )
    FakeMessageBox.information_calls = []
    monkeypatch.setattr(main_window, "choose_character_pdf", lambda qt, parent: "ravenisis.pdf")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._replace_party_member_sheet(window, FakeQt, app, state, "vale")

    assert saved_characters[-1].character_id == "vale"
    assert saved_characters[-1].name == "Ravenisis"
    assert state.selected_character_id == "vale"
    assert FakeMessageBox.information_calls[-1][1] == "Character Sheet Updated"


def test_replace_party_member_sheet_url_saves_over_existing_character(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter", selected_character_id="vale")
    saved_characters = []
    app = SimpleNamespace(
        character_imports=SimpleNamespace(
            preview_url=lambda url: CharacterImportDraft("Ravenisis", hit_points=HitPoints(8, 8))
        ),
        characters=SimpleNamespace(save=saved_characters.append),
    )
    FakeMessageBox.information_calls = []
    monkeypatch.setattr(
        main_window,
        "ask_character_url",
        lambda qt, parent: "https://example.test/ravenisis.pdf",
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._replace_party_member_sheet(window, FakeQt, app, state, "vale", "url")

    assert saved_characters[-1].character_id == "vale"
    assert saved_characters[-1].name == "Ravenisis"
    assert state.selected_character_id == "vale"
    assert FakeMessageBox.information_calls[-1][1] == "Character Sheet Updated"


def test_remove_party_member_updates_campaign_and_selection(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(
        active_campaign_id="starter",
        selected_character_id="vale",
        party_leader_character_id="vale",
        party_initiative={"vale": 18, "bran": 11},
    )
    saved_campaigns = []
    app = SimpleNamespace(
        campaigns=SimpleNamespace(
            load=lambda campaign_id: Campaign(
                campaign_id,
                "Starter",
                character_ids=("vale", "bran"),
            ),
            save=saved_campaigns.append,
        )
    )
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._remove_party_member(window, FakeQt, app, state, "vale")

    assert saved_campaigns[-1].character_ids == ("bran",)
    assert state.selected_character_id == "bran"
    assert state.party_leader_character_id == "bran"
    assert state.party_initiative == {"bran": 11}
    assert window.status.message == "Removed vale from party."


def test_set_party_initiative_refreshes_state(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter", selected_character_id="vale")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._set_party_initiative(window, FakeQt, object(), state, "vale", 22)

    assert state.party_initiative == {"vale": 22}
    assert window.status.message == "Set vale initiative to 22."
