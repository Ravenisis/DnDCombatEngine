"""Tests for the visual polyhedral dice bar."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dnd_combat_engine.gui.dice_bar import (
    DICE_OPTIONS,
    DiceBarWidget,
    InitiativeRollWidget,
    _icon_path,
)
from dnd_combat_engine.models import Character, HitPoints


class FakeSignal:
    """Minimal Qt signal test double."""

    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback

    def emit(self) -> None:
        assert self.callback is not None
        self.callback()


class FakeWidget:
    """Minimal widget test double."""

    def __init__(self) -> None:
        self.object_name = ""

    def setObjectName(self, name: str) -> None:  # noqa: N802
        self.object_name = name


class FakeLayout:
    """Record dice layout configuration."""

    def __init__(self, parent) -> None:
        parent.layout = self
        self.widgets = []
        self.alignment = None
        self.margins = None
        self.spacing = None

    def addWidget(self, widget) -> None:  # noqa: N802
        self.widgets.append(widget)

    def setAlignment(self, alignment) -> None:  # noqa: N802
        self.alignment = alignment

    def setContentsMargins(self, *margins) -> None:  # noqa: N802
        self.margins = margins

    def setSpacing(self, spacing: int) -> None:  # noqa: N802
        self.spacing = spacing


class FakeButton(FakeWidget):
    """Record visual button state and click callbacks."""

    def __init__(self) -> None:
        super().__init__()
        self.clicked = FakeSignal()
        self.text = ""
        self.tooltip = ""
        self.icon = None
        self.icon_size = None
        self.fixed_size = None
        self.tool_style = None
        self.enabled = True

    def setText(self, text: str) -> None:  # noqa: N802
        self.text = text

    def setToolTip(self, tooltip: str) -> None:  # noqa: N802
        self.tooltip = tooltip

    def setIcon(self, icon) -> None:  # noqa: N802
        self.icon = icon

    def setIconSize(self, size) -> None:  # noqa: N802
        self.icon_size = size

    def setFixedSize(self, *size) -> None:  # noqa: N802
        self.fixed_size = size

    def setToolButtonStyle(self, style) -> None:  # noqa: N802
        self.tool_style = style

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802
        self.enabled = enabled


def _fake_qt():
    widgets = SimpleNamespace(
        QWidget=FakeWidget,
        QHBoxLayout=FakeLayout,
        QToolButton=FakeButton,
        QPushButton=FakeButton,
    )
    core = SimpleNamespace(
        Qt=SimpleNamespace(
            AlignmentFlag=SimpleNamespace(AlignCenter="center"),
            ToolButtonStyle=SimpleNamespace(ToolButtonTextUnderIcon="under"),
        ),
        QSize=lambda width, height: (width, height),
    )
    gui = SimpleNamespace(QIcon=lambda path: Path(path))
    return SimpleNamespace(QtWidgets=widgets, QtCore=core, QtGui=gui)


def test_dice_bar_builds_and_activates_standard_polyhedral_set() -> None:
    rolled = []

    widget = DiceBarWidget.create(_fake_qt(), rolled.append)

    assert [button.text for button in widget.layout.widgets] == [
        "d4",
        "d6",
        "d8",
        "d10",
        "d12",
        "d20",
        "d100",
    ]
    assert all(button.icon.exists() for button in widget.layout.widgets)
    assert all("Combat Workspace" in button.tooltip for button in widget.layout.widgets)
    assert all(button.fixed_size == (68, 72) for button in widget.layout.widgets)
    widget.layout.widgets[5].clicked.emit()
    assert rolled == ["1d20"]


def test_dice_icon_catalog_matches_supported_dice() -> None:
    assert all(_icon_path(sides).is_file() for sides in DICE_OPTIONS)


def test_initiative_button_uses_character_modifier_and_activates() -> None:
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(10, 10),
        initiative_modifier=4,
    )
    app = SimpleNamespace(characters=SimpleNamespace(load=lambda character_id: character))
    activated = []

    button = InitiativeRollWidget.create(app, _fake_qt(), "ravenisis", lambda: activated.append(1))

    assert button.text == "Initiative\n+4"
    assert button.object_name == "InitiativeRollButton"
    assert button.enabled
    button.clicked.emit()
    assert activated == [1]


def test_initiative_button_disables_without_party_leader() -> None:
    app = SimpleNamespace(characters=SimpleNamespace(load=lambda character_id: None))

    button = InitiativeRollWidget.create(app, _fake_qt(), None)

    assert button.text == "Initiative\n--"
    assert not button.enabled
