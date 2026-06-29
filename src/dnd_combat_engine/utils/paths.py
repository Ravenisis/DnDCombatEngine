"""Runtime path helpers for source and installed builds."""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

APP_NAME = "DnDCombatEngine"


def bundled_data_root() -> Path:
    """Return the packaged seed-data directory, falling back to the source tree."""
    package_data = resources.files("dnd_combat_engine").joinpath("data")
    package_path = Path(str(package_data))
    if package_path.exists():
        return package_path
    return Path(__file__).resolve().parents[3] / "data"


def user_data_root() -> Path:
    """Return the writable user data directory for installed app state."""
    override = os.environ.get("DND_COMBAT_ENGINE_DATA")
    if override:
        return Path(override)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME / "data"
    return Path.home() / ".local" / "share" / "dnd-combat-engine" / "data"


def initialize_user_data(target: Path | str | None = None) -> Path:
    """Seed a writable user data directory if it does not already contain data."""
    destination = Path(target) if target is not None else user_data_root()
    source = bundled_data_root()
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.is_dir():
            for source_file in item.rglob("*.json"):
                target_file = destination / item.name / source_file.relative_to(item)
                target_file.parent.mkdir(parents=True, exist_ok=True)
                if not target_file.exists():
                    target_file.write_bytes(source_file.read_bytes())
    return destination


def default_data_root() -> Path:
    """Return the best data root for the current runtime."""
    env_root = os.environ.get("DND_COMBAT_ENGINE_DATA")
    if env_root:
        return initialize_user_data(env_root)
    source_tree_data = Path.cwd() / "data"
    if source_tree_data.exists():
        return source_tree_data
    return initialize_user_data()
