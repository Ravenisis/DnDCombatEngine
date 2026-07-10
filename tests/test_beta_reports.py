from datetime import UTC, datetime

import pytest

from dnd_combat_engine.controllers import BetaReportController
from dnd_combat_engine.models import BetaBugReport
from dnd_combat_engine.services import BetaReportService


def test_beta_report_service_appends_markdown_report(tmp_path) -> None:
    report_file = tmp_path / "BETA_TESTER_REPORTS.md"
    report = BetaBugReport(
        summary="Action bar button does not fire",
        description="Clicking slot 1 does nothing.",
        steps_to_reproduce="1. Start combat\n2. Click slot 1",
        expected_result="The selected action resolves.",
        actual_result="Nothing happens.",
        severity="High",
        area="Action Bar",
        tester_name="Ravenisis",
        created_at=datetime(2026, 7, 7, 12, 30, tzinfo=UTC),
    )

    written = BetaReportService().append_report(report_file, report)

    text = report_file.read_text(encoding="utf-8")
    assert written == report_file
    assert "# Beta Tester Reports" in text
    assert "## 2026-07-07T12:30:00+00:00 - Action bar button does not fire" in text
    assert "- Severity: High" in text
    assert "- Area: Action Bar" in text
    assert "Clicking slot 1 does nothing." in text


def test_beta_report_controller_uses_configured_report_file(tmp_path) -> None:
    report_file = tmp_path / "reports.md"
    controller = BetaReportController(BetaReportService(), report_file)

    result = controller.submit_bug_report(
        BetaBugReport("Summary", "Description", created_at=datetime(2026, 7, 7, tzinfo=UTC))
    )

    assert result == report_file
    assert "Summary" in report_file.read_text(encoding="utf-8")


def test_beta_bug_report_requires_summary_and_description() -> None:
    with pytest.raises(ValueError, match="summary"):
        BetaBugReport("", "Description")
    with pytest.raises(ValueError, match="description"):
        BetaBugReport("Summary", "")
