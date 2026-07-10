"""Beta tester report persistence."""

from __future__ import annotations

from pathlib import Path

from dnd_combat_engine.models.beta_reports import BetaBugReport


class BetaReportService:
    """Append beta tester reports to a markdown report file."""

    def append_report(self, report_file: Path | str, report: BetaBugReport) -> Path:
        """Append a report to a markdown file and return the written path."""
        path = Path(report_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if path.exists() and path.stat().st_size else _report_file_header()
        with path.open("a", encoding="utf-8") as file:
            file.write(prefix)
            file.write(_report_to_markdown(report))
        return path


def _report_file_header() -> str:
    return (
        "# Beta Tester Reports\n\n"
        "This file collects tester-submitted reports while GitHub issue creation is\n"
        "restricted. Do not paste access tokens, passwords, private campaign notes, or\n"
        "other secrets into reports.\n\n"
    )


def _report_to_markdown(report: BetaBugReport) -> str:
    timestamp = report.timestamp.isoformat(timespec="seconds")
    return (
        f"## {timestamp} - {_clean_line(report.summary)}\n\n"
        f"- Severity: {_clean_line(report.severity)}\n"
        f"- Area: {_clean_line(report.area)}\n"
        f"- Version: {_clean_line(report.app_version)}\n"
        f"- Tester: {_clean_line(report.tester_name) or 'Not provided'}\n\n"
        "### Description\n\n"
        f"{_clean_block(report.description)}\n\n"
        "### Steps To Reproduce\n\n"
        f"{_clean_block(report.steps_to_reproduce) or 'Not provided.'}\n\n"
        "### Expected Result\n\n"
        f"{_clean_block(report.expected_result) or 'Not provided.'}\n\n"
        "### Actual Result\n\n"
        f"{_clean_block(report.actual_result) or 'Not provided.'}\n\n"
    )


def _clean_line(value: str) -> str:
    return " ".join(value.strip().splitlines())


def _clean_block(value: str) -> str:
    return value.strip()
