from dnd_combat_engine.gui import main_window


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


def test_pdf_menu_action_runs_import_and_reports_status(monkeypatch) -> None:
    window = FakeWindow()
    FakeMessageBox.information_calls = []
    monkeypatch.setattr(main_window, "choose_character_pdf", lambda qt, parent: "sheet.pdf")
    monkeypatch.setattr(
        main_window,
        "import_character_pdf_to_campaign",
        lambda app, campaign_id, path: f"Imported from {path}.",
    )

    main_window._run_menu_action(window, FakeQt, object(), "campaign.import_pdf")

    assert window.status.message == "Imported from sheet.pdf."
    assert FakeMessageBox.information_calls[-1][1] == "Character Imported"


def test_url_menu_action_runs_import_and_reports_errors(monkeypatch) -> None:
    window = FakeWindow()
    FakeMessageBox.warning_calls = []
    monkeypatch.setattr(main_window, "ask_character_url", lambda qt, parent: "https://example.test")

    def fail_import(app, campaign_id, url):
        raise ValueError("could not import")

    monkeypatch.setattr(main_window, "import_character_url_to_campaign", fail_import)

    main_window._run_menu_action(window, FakeQt, object(), "campaign.import_url")

    assert window.status.message == "could not import"
    assert FakeMessageBox.warning_calls[-1][1] == "Import Failed"

