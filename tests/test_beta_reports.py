from datetime import UTC, datetime

import pytest

from dnd_combat_engine.controllers import BetaReportController
from dnd_combat_engine.models import BetaBugReport
from dnd_combat_engine.services import BetaReportService, beta_report_service


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

    assert result == str(report_file)
    assert "Summary" in report_file.read_text(encoding="utf-8")


def test_beta_report_service_submits_to_github_when_token_is_configured(monkeypatch) -> None:
    calls = []
    existing = "# Beta Tester Reports\n\n"
    encoded = beta_report_service.base64.b64encode(existing.encode("utf-8")).decode("ascii")

    class Response:
        def __init__(self, payload: dict[str, object] | None = None) -> None:
            self.payload = payload or {}

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def read(self) -> bytes:
            return beta_report_service.json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request, timeout):
        calls.append(request)
        if request.get_method() == "GET":
            return Response({"content": encoded, "sha": "abc123"})
        return Response()

    monkeypatch.setenv("DND_COMBAT_ENGINE_GITHUB_TOKEN", "token")
    monkeypatch.setenv("DND_COMBAT_ENGINE_BUG_REPORT_REPO", "Ravenisis/DnDCombatEngine")
    monkeypatch.setattr(beta_report_service, "urlopen", fake_urlopen)

    result = BetaReportService().submit_report(
        "unused.md",
        BetaBugReport("Online summary", "Online description"),
    )

    assert result == "https://github.com/Ravenisis/DnDCombatEngine/blob/main/BETA_TESTER_REPORTS.md"
    assert [call.get_method() for call in calls] == ["GET", "PUT"]
    put_payload = beta_report_service.json.loads(calls[-1].data.decode("utf-8"))
    uploaded = beta_report_service.base64.b64decode(put_payload["content"]).decode("utf-8")
    assert "Online summary" in uploaded
    assert put_payload["sha"] == "abc123"


def test_beta_report_service_falls_back_to_local_file_when_online_submission_fails(
    monkeypatch,
    tmp_path,
) -> None:
    def fail_urlopen(request, timeout):
        raise OSError("offline")

    report_file = tmp_path / "reports.md"
    monkeypatch.setenv("DND_COMBAT_ENGINE_GITHUB_TOKEN", "token")
    monkeypatch.setattr(beta_report_service, "urlopen", fail_urlopen)

    result = BetaReportService().submit_report(
        report_file,
        BetaBugReport("Fallback summary", "Fallback description"),
    )

    assert result == str(report_file)
    assert "Fallback summary" in report_file.read_text(encoding="utf-8")


def test_beta_bug_report_requires_summary_and_description() -> None:
    with pytest.raises(ValueError, match="summary"):
        BetaBugReport("", "Description")
    with pytest.raises(ValueError, match="description"):
        BetaBugReport("Summary", "")
