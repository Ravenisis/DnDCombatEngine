
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
            self.widgets = []

        def addWidget(self, widget) -> None:
            self.widgets.append(widget)
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
    assert "Spellbook" not in window._dnd_docks
    assert "Spellbook" not in window._dnd_panel_hosts
    assert "Abilities" in window._dnd_panel_hosts
    assert "Action Bar" in window._dnd_docks


def test_action_bar_remove_gesture_requires_shift_right_click() -> None:
    from dnd_combat_engine.gui.widgets import _is_shift_left_click, _is_shift_right_click

    class FakeMouseButton:
        LeftButton = 1
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
    assert _is_shift_left_click(FakeQt, FakeEvent(1, 1)) is True
    assert _is_shift_left_click(FakeQt, FakeEvent(1, 0)) is False
    assert _is_shift_left_click(FakeQt, FakeEvent(2, 1)) is False


def test_action_bar_button_text_wraps_with_hotkey_first() -> None:
    from dnd_combat_engine.gui.widgets import _action_button_text
    from dnd_combat_engine.models import ActionBarActionKind, ActionBarButton

    button = ActionBarButton(
        slot=1,
        kind=ActionBarActionKind.SPELL,
        action_id="mass_healing_word",
        name="Mass Healing Word",
        rank=3,
    )

    lines = _action_button_text("1", button).splitlines()

    assert lines[0] == "1"
    assert len(lines) <= 4
    assert all(len(line) <= 10 for line in lines[1:])
    assert _action_button_text("2", None) == "2\nEmpty"


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

    assert _initiative_text(None) == "Initiative: - | Position: -"
    assert _initiative_text(17) == "Initiative: 17 | Position: 1"
    assert _initiative_text("vale", {"bran": 11, "vale": 18}) == (
        "Initiative: 18 | Position: 1"
    )
    assert _initiative_text("bran", {"bran": 11, "vale": 18}) == (
        "Initiative: 11 | Position: 2"
    )
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


def test_spellbook_spell_ids_filter_to_character_features() -> None:
    from types import SimpleNamespace

    from dnd_combat_engine.gui import widgets
    from dnd_combat_engine.models import Character, HitPoints, Spell, SpellSchool

    spells = {
        "bless": Spell(
            "bless",
            "Bless",
            1,
            SpellSchool.ENCHANTMENT,
            "1 action",
            "30 feet",
            "1 minute",
        ),
        "hex": Spell(
            "hex",
            "Hex",
            1,
            SpellSchool.ENCHANTMENT,
            "1 bonus action",
            "90 feet",
            "1 hour",
        ),
    }
    character = Character(
        "cleric",
        "Cleric",
        HitPoints(10, 10),
        features=("Domain Spells: Bless",),
    )
    app = SimpleNamespace(
        characters=SimpleNamespace(load=lambda character_id: character),
        compendium=SimpleNamespace(
            persistence_service=SimpleNamespace(list_spell_ids=lambda: ["bless", "hex"]),
            load_spell=lambda spell_id: spells[spell_id],
        ),
    )

    assert widgets._spell_ids_for_character(app, "cleric") == ("bless",)


def test_spell_slot_rows_are_sorted_by_slot_level() -> None:
    from dnd_combat_engine.gui.widgets import _spell_slot_rows
    from dnd_combat_engine.models import ResourcePool

    rows = _spell_slot_rows(
        {
            "hit_dice": ResourcePool("hit_dice", 1, 1),
            "spell_slot_3": ResourcePool("spell_slot_3", 2, 3),
            "spell_slot_1": ResourcePool("spell_slot_1", 4, 4),
        }
    )

    assert rows == ((1, 4, 4), (3, 2, 3))


def test_main_workspace_uses_scrollable_left_splitter() -> None:
    from types import SimpleNamespace

    from dnd_combat_engine.gui import main_window

    class FakeOrientation:
        Horizontal = 1

    class FakeQtNamespace:
        Orientation = FakeOrientation

    class FakeQtCore:
        Qt = FakeQtNamespace

    class FakeWidget:
        def setMinimumWidth(self, value) -> None:  # noqa: N802
            self.minimum_width = value

    class FakeLayout:
        def __init__(self, parent) -> None:
            self.parent = parent
            self.margins = None
            self.spacing = None

        def setContentsMargins(self, *values) -> None:  # noqa: N802
            self.margins = values

        def setSpacing(self, value) -> None:  # noqa: N802
            self.spacing = value

    class FakeScroll:
        def setMinimumWidth(self, value) -> None:  # noqa: N802
            self.minimum_width = value

        def setMaximumWidth(self, value) -> None:  # noqa: N802
            self.maximum_width = value

        def setWidgetResizable(self, value) -> None:  # noqa: N802
            self.resizable = value

        def setWidget(self, widget) -> None:  # noqa: N802
            self.widget = widget

    class FakeSplitter:
        def __init__(self, orientation) -> None:
            self.orientation = orientation
            self.widgets = []
            self.stretch = {}
            self.sizes = None
            self.collapsible = {}

        def addWidget(self, widget) -> None:  # noqa: N802
            self.widgets.append(widget)

        def setStretchFactor(self, index, value) -> None:  # noqa: N802
            self.stretch[index] = value

        def setSizes(self, sizes) -> None:  # noqa: N802
            self.sizes = sizes

        def setCollapsible(self, index, value) -> None:  # noqa: N802
            self.collapsible[index] = value

    class FakeQtWidgets:
        QWidget = FakeWidget
        QVBoxLayout = FakeLayout
        QScrollArea = FakeScroll
        QSplitter = FakeSplitter

    qt = SimpleNamespace(QtCore=FakeQtCore, QtWidgets=FakeQtWidgets)
    window = SimpleNamespace()
    workspace = FakeWidget()

    splitter = main_window._main_workspace(window, qt, workspace)

    assert splitter.orientation == 1
    assert len(splitter.widgets) == 2
    assert splitter.widgets[0].resizable is True
    assert splitter.widgets[0].minimum_width == 520
    assert splitter.widgets[0].maximum_width == 980
    assert splitter.widgets[1] is workspace
    assert workspace.minimum_width == 360
    assert splitter.collapsible == {0: False, 1: False}
    assert splitter.stretch == {0: 2, 1: 1}
    assert splitter.sizes == [800, 400]
    assert window._dnd_left_layout.margins == (6, 6, 6, 6)


def test_panel_replacement_swaps_stored_widget() -> None:
    from types import SimpleNamespace

    from dnd_combat_engine.gui import main_window

    class FakeLayout:
        def __init__(self) -> None:
            self.removed = []
            self.added = []

        def removeWidget(self, widget) -> None:  # noqa: N802
            self.removed.append(widget)

        def addWidget(self, widget) -> None:  # noqa: N802
            self.added.append(widget)

    class FakeWidget:
        def setParent(self, parent) -> None:  # noqa: N802
            self.parent = parent

    old_widget = FakeWidget()
    host = SimpleNamespace(_dnd_panel_layout=FakeLayout(), _dnd_panel_widget=old_widget)
    new_widget = FakeWidget()

    main_window._replace_panel_widget({"Party": host}, "Party", new_widget)

    assert host._dnd_panel_layout.removed == [old_widget]
    assert host._dnd_panel_layout.added == [new_widget]
    assert old_widget.parent is None
    assert host._dnd_panel_widget is new_widget


def test_action_bar_widget_includes_spell_slot_tracker(monkeypatch) -> None:
    from types import SimpleNamespace

    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.action_bar import ActionBarSession
    from dnd_combat_engine.models import Character, HitPoints, ResourcePool

    class FakeWidget:
        pass

    class FakeLayout:
        def __init__(self, parent) -> None:
            self.parent = parent
            self.widgets = []
            parent.layout = self

        def addWidget(self, widget, stretch=None) -> None:  # noqa: N802
            self.widgets.append((widget, stretch))

    class FakeQtWidgets:
        QWidget = FakeWidget
        QHBoxLayout = FakeLayout

    qt = SimpleNamespace(QtWidgets=FakeQtWidgets)
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(10, 10),
        resources={"spell_slot_1": ResourcePool("spell_slot_1", 4, 4)},
    )
    app = SimpleNamespace(characters=SimpleNamespace(load=lambda character_id: character))
    monkeypatch.setattr(main_window.ActionBarWidget, "create", lambda *args, **kwargs: "bar")
    monkeypatch.setattr(
        main_window.SpellSlotTrackerWidget,
        "create",
        lambda *args, **kwargs: "slots",
    )

    widget = main_window._action_bar_widget(
        app,
        qt,
        main_window.GuiCampaignState(party_leader_character_id="ravenisis"),
        ActionBarSession(),
        lambda *args: None,
    )

    assert widget is not None
    assert widget.layout.widgets == [("slots", None), ("bar", 1)]


def test_layout_helpers_cover_fallback_paths() -> None:
    from types import SimpleNamespace

    from dnd_combat_engine.gui import main_window

    class OneArgLayout:
        def __init__(self, parent=None) -> None:
            self.parent = parent
            self.widgets = []

        def addWidget(self, widget) -> None:  # noqa: N802
            self.widgets.append(widget)

    class StretchRejectingLayout(OneArgLayout):
        def addWidget(self, widget, stretch=None) -> None:  # noqa: N802
            if stretch is not None:
                raise TypeError
            self.widgets.append(widget)

    class FakeWidget:
        pass

    class FakeQtWidgets:
        QWidget = FakeWidget
        QVBoxLayout = OneArgLayout

    qt = SimpleNamespace(QtWidgets=FakeQtWidgets)
    widget = FakeWidget()
    assert main_window._scroll_area(qt, widget) is widget

    no_layout_window = SimpleNamespace()
    main_window._add_left_panel(no_layout_window, qt, "Missing", widget)

    layout = OneArgLayout()
    window = SimpleNamespace(_dnd_left_layout=layout, _dnd_panel_hosts={})
    main_window._add_left_panel(window, qt, "Panel", widget)
    assert "Panel" in window._dnd_panel_hosts
    assert layout.widgets

    stretch_layout = StretchRejectingLayout()
    main_window._layout_add_widget(stretch_layout, "child", 1)
    assert stretch_layout.widgets == ["child"]

    main_window._replace_panel_widget({}, "Missing", widget)


def test_spell_slot_tracker_handles_empty_and_missing_leaders() -> None:
    from types import SimpleNamespace

    from dnd_combat_engine.gui.widgets import SpellSlotTrackerWidget

    class FakeWidget:
        def __init__(self, *args) -> None:
            self.args = args

    class FakeLabel(FakeWidget):
        pass

    class FakeLayout:
        def __init__(self, parent) -> None:
            parent.layout = self
            self.widgets = []

        def addWidget(self, widget) -> None:  # noqa: N802
            self.widgets.append(widget)

    class FakeQtWidgets:
        QWidget = FakeWidget
        QLabel = FakeLabel
        QVBoxLayout = FakeLayout

    qt = SimpleNamespace(QtWidgets=FakeQtWidgets)

    def missing_character(character_id):
        raise KeyError(character_id)

    app = SimpleNamespace(characters=SimpleNamespace(load=missing_character))

    no_leader = SpellSlotTrackerWidget.create(app, qt, None)
    missing_leader = SpellSlotTrackerWidget.create(app, qt, "missing")

    assert [widget.args[0] for widget in no_leader.layout.widgets] == [
        "Spell Slots",
        "No leader",
    ]
    assert [widget.args[0] for widget in missing_leader.layout.widgets] == [
        "Spell Slots",
        "Missing leader",
    ]

