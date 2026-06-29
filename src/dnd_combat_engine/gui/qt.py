"""Qt import helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class GuiDependencyError(RuntimeError):
    """Raised when PySide6 is required but not installed."""


@dataclass(frozen=True, slots=True)
class QtModules:
    """Imported PySide6 modules used by the GUI."""

    QtCore: Any
    QtGui: Any
    QtWidgets: Any


def load_qt() -> QtModules:
    """Load PySide6 modules or raise a helpful dependency error."""
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise GuiDependencyError(
            'PySide6 is not installed. Install GUI dependencies with: pip install ".[gui]"'
        ) from exc
    return QtModules(QtCore=QtCore, QtGui=QtGui, QtWidgets=QtWidgets)
