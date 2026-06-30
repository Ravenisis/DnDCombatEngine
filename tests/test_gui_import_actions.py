from types import SimpleNamespace

from dnd_combat_engine.gui import main_window
from dnd_combat_engine.models import Campaign, Character, HitPoints
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


def _import_result() -> SimpleNamespace:
    character = Character("lyra", "Lyra", HitPoints(10, 10))
    campaign = Campaign("starter", "Starter", character_ids=("lyra",))
    return SimpleNamespace(character=character, campaign=campaign)


def test_pdf_menu_action_runs_import_and_reports_status(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter", selected_character_id=None)
    app = SimpleNamespace(
        character_imports=SimpleNamespace(
            import_pdf_to_campaign=lambda path, campaign_id: _import_result()
        )
    )
    FakeMessageBox.information_calls = []
    monkeypatch.setattr(main_window, "choose_character_pdf", lambda qt, parent: "sheet.pdf")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, app, state, "campaign.import_pdf")

    assert window.status.message == "Imported Lyra as lyra and added them to Starter."
    assert state.selected_character_id == "lyra"
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


def test_close_campaign_clears_active_state(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter", selected_character_id="vale")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._run_menu_action(window, FakeQt, object(), state, "campaign.close")

    assert state.active_campaign_id is None
    assert state.selected_character_id is None
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
    assert window.status.message == "Created Storm Coast."


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


def test_remove_party_member_updates_campaign_and_selection(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(
        active_campaign_id="starter",
        selected_character_id="vale",
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
    assert state.party_initiative == {"bran": 11}
    assert window.status.message == "Removed vale from party."


def test_set_party_initiative_refreshes_state(monkeypatch) -> None:
    window = FakeWindow()
    state = main_window.GuiCampaignState(active_campaign_id="starter", selected_character_id="vale")
    monkeypatch.setattr(main_window, "_refresh_campaign_docks", lambda *args: None)

    main_window._set_party_initiative(window, FakeQt, object(), state, "vale", 22)

    assert state.party_initiative == {"vale": 22}
    assert window.status.message == "Set vale initiative to 22."
