"""GUI session persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Self


@dataclass(frozen=True, slots=True)
class GuiSession:
    """Persisted GUI session settings."""

    data_root: str = "data"
    last_character_id: str = "vale"
    window_width: int = 1200
    window_height: int = 800

    def __post_init__(self) -> None:
        """Validate session settings."""
        if not self.data_root:
            raise ValueError("data_root is required")
        if not self.last_character_id:
            raise ValueError("last_character_id is required")
        if self.window_width < 640:
            raise ValueError("window_width must be at least 640")
        if self.window_height < 480:
            raise ValueError("window_height must be at least 480")

    def to_dict(self) -> dict[str, object]:
        """Serialize session settings to plain JSON-compatible data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build session settings from JSON-compatible data."""
        return cls(
            data_root=str(data.get("data_root", "data")),
            last_character_id=str(data.get("last_character_id", "vale")),
            window_width=int(data.get("window_width", 1200)),
            window_height=int(data.get("window_height", 800)),
        )


def save_session(session: GuiSession, path: Path | str) -> Path:
    """Save GUI session settings and return the path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def load_session(path: Path | str) -> GuiSession:
    """Load GUI session settings or return defaults if the file is absent."""
    source = Path(path)
    if not source.exists():
        return GuiSession()
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("GUI session file must contain a JSON object")
    return GuiSession.from_dict(data)
