
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


def test_action_bar_remove_gesture_requires_shift_right_click() -> None:
    from dnd_combat_engine.gui.widgets import _is_shift_right_click

    class FakeMouseButton:
        RightButton = 2

    class FakeKeyboardModifier:
        ShiftModifier = 1

    class FakeQtNamespace:
        MouseButton = FakeMouseButton
        KeyboardModifier = FakeKeyboardModifier

    class FakeQtCore:
        Qt = FakeQtNamespace

    class FakeQt:
        QtCore = FakeQtCore

    class FakeEvent:
        def __init__(self, button: int, modifiers: int) -> None:
            self._button = button
            self._modifiers = modifiers

        def button(self) -> int:
            return self._button

        def modifiers(self) -> int:
            return self._modifiers

    assert _is_shift_right_click(FakeQt, FakeEvent(2, 1)) is True
    assert _is_shift_right_click(FakeQt, FakeEvent(2, 0)) is False
    assert _is_shift_right_click(FakeQt, FakeEvent(1, 1)) is False


def test_party_initiative_helpers_parse_and_prompt() -> None:
    from dnd_combat_engine.gui.widgets import (
        _ask_initiative_roll,
        _initiative_text,
        _parse_initiative_value,
    )

    class FakeInputDialog:
        response = (17, True)

        @classmethod
        def getInt(cls, *args):
            return cls.response

    class FakeQtWidgets:
        QInputDialog = FakeInputDialog

    class FakeQt:
        QtWidgets = FakeQtWidgets

    assert _initiative_text(None) == "Initiative: -"
    assert _initiative_text(17) == "Initiative: 17"
    assert _parse_initiative_value(" 22 ") == 22
    assert _parse_initiative_value("twenty") is None
    assert _ask_initiative_roll(FakeQt, object(), None) == 17

    FakeInputDialog.response = (0, False)
    assert _ask_initiative_roll(FakeQt, object(), 4) is None


def test_party_context_menu_wires_actions(monkeypatch) -> None:
    from dnd_combat_engine.gui import widgets

    calls = []

    class FakeSignal:
        def connect(self, callback) -> None:
            self.callback = callback

    class FakeAction:
        def __init__(self, label: str) -> None:
            self.label = label
            self.triggered = FakeSignal()

    class FakeMenu:
        last = None

        def __init__(self, parent) -> None:
            self.parent = parent
            self.actions = []
            self.position = None
            FakeMenu.last = self

        def addAction(self, label: str):
            action = FakeAction(label)
            self.actions.append(action)
            return action

        def exec(self, position) -> None:
            self.position = position

    class FakeQtWidgets:
        QMenu = FakeMenu

    class FakeQt:
        QtWidgets = FakeQtWidgets

    class FakeFrame:
        def mapToGlobal(self, position):
            return f"global:{position}"

    monkeypatch.setattr(widgets, "_ask_initiative_roll", lambda qt, parent, current: 19)

    widgets._show_party_context_menu(
        FakeQt,
        FakeFrame(),
        "point",
        "vale",
        12,
        lambda character_id: calls.append(("upload", character_id)),
        lambda character_id: calls.append(("remove", character_id)),
        lambda character_id, value: calls.append(("initiative", character_id, value)),
    )

    assert FakeMenu.last.position == "global:point"
    for action in FakeMenu.last.actions:
        action.triggered.callback()
    assert calls == [("upload", "vale"), ("remove", "vale"), ("initiative", "vale", 19)]


def test_party_context_policy_and_frame_style(monkeypatch) -> None:
    from dnd_combat_engine.gui import widgets

    captured = {}

    class FakeSignal:
        def connect(self, callback) -> None:
            self.callback = callback

    class FakeContextMenuPolicy:
        CustomContextMenu = 4

    class FakeQtNamespace:
        ContextMenuPolicy = FakeContextMenuPolicy

    class FakeQtCore:
        Qt = FakeQtNamespace

    class FakeQt:
        QtCore = FakeQtCore

    class FakeFrame:
        def __init__(self) -> None:
            self.customContextMenuRequested = FakeSignal()

        def setContextMenuPolicy(self, policy) -> None:
            self.policy = policy

    def fake_show(*args) -> None:
        captured["args"] = args

    monkeypatch.setattr(widgets, "_show_party_context_menu", fake_show)
    frame = FakeFrame()

    widgets._install_party_context_menu(
        FakeQt,
        frame,
        "vale",
        18,
        lambda character_id: None,
        None,
        None,
    )

    frame.customContextMenuRequested.callback("point")
    assert frame.policy == 4
    assert captured["args"][3:5] == ("vale", 18)

    class FakeFrameClass:
        StyledPanel = 1
        Raised = 2

    class StyledFrame:
        def setFrameShape(self, shape) -> None:
            self.shape = shape

        def setFrameShadow(self, shadow) -> None:
            self.shadow = shadow

    styled = StyledFrame()
    widgets._set_frame_style(FakeFrameClass, styled)
    assert styled.shape == 1
    assert styled.shadow == 2

