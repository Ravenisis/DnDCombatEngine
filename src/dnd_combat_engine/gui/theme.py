"""GUI theme helpers."""

from __future__ import annotations


def dark_theme_stylesheet() -> str:
    """Return the application dark theme stylesheet."""
    return """
QMainWindow, QWidget {
    background: #111318;
    color: #e7eaf0;
    font-size: 13px;
}
QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}
QDockWidget::title {
    background: #1b1f2a;
    padding: 6px;
    border-bottom: 1px solid #2d3442;
}
QTextEdit, QListWidget, QTableWidget {
    background: #171b23;
    border: 1px solid #303849;
    selection-background-color: #365a9c;
}
QPushButton {
    background: #253149;
    border: 1px solid #3a4863;
    padding: 6px 10px;
}
QPushButton:hover {
    background: #31405f;
}
"""

