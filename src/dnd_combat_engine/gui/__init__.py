"""PySide6 graphical interface layer."""

from dnd_combat_engine.gui.actions import GuiActionSpec, default_action_specs
from dnd_combat_engine.gui.commands import GuiCommandDispatcher
from dnd_combat_engine.gui.main_window import create_main_window, run_gui
from dnd_combat_engine.gui.preferences import GuiPreferences
from dnd_combat_engine.gui.qt import GuiDependencyError
from dnd_combat_engine.gui.session import GuiSession, load_session, save_session
from dnd_combat_engine.gui.theme import dark_theme_stylesheet

__all__ = [
    "GuiActionSpec",
    "GuiCommandDispatcher",
    "GuiDependencyError",
    "GuiPreferences",
    "GuiSession",
    "create_main_window",
    "dark_theme_stylesheet",
    "default_action_specs",
    "load_session",
    "run_gui",
    "save_session",
]
