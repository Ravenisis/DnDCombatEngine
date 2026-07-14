"""Tests for the visual polyhedral dice bar."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dnd_combat_engine.gui.dice_bar import DICE_OPTIONS, DiceBarWidget, _icon_path


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
        "d%",
    ]
    assert all(button.icon.exists() for button in widget.layout.widgets)
    assert all("Combat Workspace" in button.tooltip for button in widget.layout.widgets)
    widget.layout.widgets[5].clicked.emit()
    assert rolled == ["1d20"]


def test_dice_icon_catalog_matches_supported_dice() -> None:
    assert all(_icon_path(sides).is_file() for sides in DICE_OPTIONS)
