"""Beta tester report models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class BetaBugReport:
    """A tester-submitted bug report."""

    summary: str
    description: str
    steps_to_reproduce: str = ""
    expected_result: str = ""
    actual_result: str = ""
    severity: str = "Medium"
    area: str = "General"
    tester_name: str = ""
    app_version: str = "1.0.0-beta.1"
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required report fields."""
        if not self.summary.strip():
            raise ValueError("summary is required")
        if not self.description.strip():
            raise ValueError("description is required")

    @property
    def timestamp(self) -> datetime:
        """Return the report creation timestamp."""
        return self.created_at or datetime.now(UTC)
