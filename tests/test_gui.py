
from dnd_combat_engine.gui import GuiDependencyError, dark_theme_stylesheet
from dnd_combat_engine.gui.qt import load_qt


def test_dark_theme_contains_expected_widget_rules() -> None:
    stylesheet = dark_theme_stylesheet()

    assert "QMainWindow" in stylesheet
    assert "QDockWidget" in stylesheet
    assert "#111318" in stylesheet


def test_load_qt_raises_helpful_error_when_pyside6_is_missing() -> None:
    try:
        modules = load_qt()
    except GuiDependencyError as exc:
        assert "pip install" in str(exc)
    else:
        assert modules.QtCore is not None
        assert modules.QtGui is not None
        assert modules.QtWidgets is not None


def test_main_window_uses_qt_loader(monkeypatch) -> None:
    from dnd_combat_engine.gui import main_window

    class FakeAlignmentFlag:
        AlignCenter = 1

    class FakeDockWidgetArea:
        LeftDockWidgetArea = 1
        BottomDockWidgetArea = 2

    class FakeQt:
        AlignmentFlag = FakeAlignmentFlag
        DockWidgetArea = FakeDockWidgetArea

    class FakeQtCore:
        Qt = FakeQt

    class FakeQtGui:
        pass

    class FakeWidget:
        def __init__(self, *args) -> None:
            self.args = args

        def setReadOnly(self, value) -> None:
            self.read_only = value

        def append(self, value) -> None:
            self.appended = value

        def text(self) -> str:
            return self.args[0] if self.args else ""

        def setAlignment(self, value) -> None:
            self.alignment = value

        def setHorizontalHeaderLabels(self, labels) -> None:
            self.labels = labels

        def setItem(self, row, column, item) -> None:
            self.item = (row, column, item)

        def setText(self, value) -> None:
            self.text_value = value

        def setEnabled(self, value) -> None:
            self.enabled = value

        def setToolTip(self, value) -> None:
            self.tooltip = value

        def setFixedSize(self, width, height) -> None:
            self.fixed_size = (width, height)

        def setShortcut(self, value) -> None:
            self.shortcut = value

    class FakeLayout:
        def __init__(self, widget) -> None:
            self.widget = widget

        def addWidget(self, widget) -> None:
            self.widget = widget

        def setAlignment(self, value) -> None:
            self.alignment = value

    class FakeSignal:
        def connect(self, callback) -> None:
            self.callback = callback

    class FakeButton(FakeWidget):
        clicked = FakeSignal()

    class FakeMainWindow(FakeWidget):
        def setWindowTitle(self, title) -> None:
            self.title = title

        def resize(self, width, height) -> None:
            self.size = (width, height)

        def setStyleSheet(self, stylesheet) -> None:
            self.stylesheet = stylesheet

        def setCentralWidget(self, widget) -> None:
            self.central = widget

        def addDockWidget(self, area, dock) -> None:
            self.dock = (area, dock)

        def menuBar(self):
            return FakeMenuBar()

        def statusBar(self):
            return FakeStatusBar()

    class FakeDockWidget(FakeWidget):
        def setWidget(self, widget) -> None:
            self.widget = widget

    class FakeMenu:
        def addMenu(self, name):
            self.submenu_name = name
            return FakeMenu()

        def addAction(self, action) -> None:
            self.action = action

    class FakeMenuBar:
        def addMenu(self, name):
            self.name = name
            return FakeMenu()

    class FakeStatusBar:
        def showMessage(self, message) -> None:
            self.message = message

    class FakeQtWidgets:
        QMainWindow = FakeMainWindow
        QLabel = FakeWidget
        QDockWidget = FakeDockWidget
        QWidget = FakeWidget
        QVBoxLayout = FakeLayout
        QHBoxLayout = FakeLayout
        QLineEdit = FakeWidget
        QPushButton = FakeButton
        QTextEdit = FakeWidget
        QTableWidget = FakeWidget
        QTableWidgetItem = FakeWidget

    FakeQtGui.QAction = FakeWidget

    class FakeModules:
        QtCore = FakeQtCore
        QtGui = FakeQtGui
        QtWidgets = FakeQtWidgets

    monkeypatch.setattr(main_window, "load_qt", lambda: FakeModules)

    window = main_window.create_main_window()

    assert window.title == "DnDCombatEngine"
    assert window.size == (1200, 800)

