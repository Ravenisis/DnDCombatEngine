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


def parchment_theme_stylesheet() -> str:
    """Return a light parchment-inspired stylesheet."""
    return """
QMainWindow, QWidget {
    background: #f1eadc;
    color: #211b16;
    font-size: 13px;
}
QDockWidget::title {
    background: #d8c9ad;
    padding: 6px;
    border-bottom: 1px solid #a99068;
}
QTextEdit, QListWidget, QTableWidget {
    background: #fffaf0;
    border: 1px solid #b59d78;
    selection-background-color: #b88746;
}
QPushButton {
    background: #d1b47e;
    border: 1px solid #8b7047;
    padding: 6px 10px;
}
QPushButton:hover {
    background: #c5a267;
}
"""


def high_contrast_theme_stylesheet() -> str:
    """Return a high-contrast dark stylesheet."""
    return """
QMainWindow, QWidget {
    background: #000000;
    color: #ffffff;
    font-size: 13px;
}
QDockWidget::title {
    background: #202020;
    padding: 6px;
    border-bottom: 1px solid #808080;
}
QTextEdit, QListWidget, QTableWidget {
    background: #050505;
    border: 1px solid #ffffff;
    selection-background-color: #005bbb;
}
QPushButton {
    background: #1d3557;
    border: 1px solid #ffffff;
    padding: 6px 10px;
}
QPushButton:hover {
    background: #2f5d95;
}
"""
