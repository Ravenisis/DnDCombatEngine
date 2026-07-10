"""UI-facing beta report workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dnd_combat_engine.models.beta_reports import BetaBugReport
from dnd_combat_engine.services.beta_report_service import BetaReportService


@dataclass(frozen=True, slots=True)
class BetaReportController:
    """Coordinate beta tester report submission."""

    report_service: BetaReportService
    report_file: Path

    def submit_bug_report(self, report: BetaBugReport) -> str:
        """Submit a bug report online when configured, otherwise save locally."""
        return self.report_service.submit_report(self.report_file, report)
