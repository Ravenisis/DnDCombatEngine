"""Packaged GUI executable entry point."""

from __future__ import annotations

from dnd_combat_engine.gui import GuiDependencyError, run_gui
from dnd_combat_engine.utils.paths import default_data_root


def main() -> int:
    """Run the GUI with install-safe data initialization."""
    try:
        return run_gui(default_data_root())
    except GuiDependencyError as exc:
        print(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
