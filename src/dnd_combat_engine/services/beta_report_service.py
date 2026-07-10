"""Beta tester report persistence."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dnd_combat_engine.models.beta_reports import BetaBugReport


class BetaReportService:
    """Append beta tester reports to a markdown report file."""

    def submit_report(self, report_file: Path | str, report: BetaBugReport) -> str:
        """Submit a report online when configured, otherwise append it locally."""
        token = os.environ.get("DND_COMBAT_ENGINE_GITHUB_TOKEN", "").strip()
        if token:
            try:
                return self.submit_report_to_github(report, token)
            except (OSError, ValueError):
                return str(self.append_report(report_file, report))
        return str(self.append_report(report_file, report))

    def append_report(self, report_file: Path | str, report: BetaBugReport) -> Path:
        """Append a report to a markdown file and return the written path."""
        path = Path(report_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if path.exists() and path.stat().st_size else _report_file_header()
        with path.open("a", encoding="utf-8") as file:
            file.write(prefix)
            file.write(_report_to_markdown(report))
        return path

    def submit_report_to_github(self, report: BetaBugReport, token: str) -> str:
        """Append a report to the configured GitHub repository file."""
        target = _github_report_target()
        current = _github_get_file(target, token)
        existing_text = current.get("text", "")
        prefix = "" if existing_text.strip() else _report_file_header()
        next_text = f"{existing_text}{prefix}{_report_to_markdown(report)}"
        _github_put_file(target, token, next_text, current.get("sha"))
        return (
            f"https://github.com/{target['repo']}/blob/"
            f"{target['branch']}/{target['path']}"
        )


def _github_report_target() -> dict[str, str]:
    repo = os.environ.get("DND_COMBAT_ENGINE_BUG_REPORT_REPO", "Ravenisis/DnDCombatEngine")
    branch = os.environ.get("DND_COMBAT_ENGINE_BUG_REPORT_BRANCH", "main")
    path = os.environ.get("DND_COMBAT_ENGINE_BUG_REPORT_PATH", "BETA_TESTER_REPORTS.md")
    return {
        "repo": repo.strip(),
        "branch": branch.strip(),
        "path": path.strip().lstrip("/"),
    }


def _github_get_file(target: dict[str, str], token: str) -> dict[str, str | None]:
    request = _github_request(
        target,
        token,
        method="GET",
        query=f"?ref={target['branch']}",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return {"text": "", "sha": None}
        raise ValueError(f"GitHub bug report fetch failed with HTTP {exc.code}.") from exc
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise OSError("GitHub bug report fetch failed.") from exc
    content = str(payload.get("content", ""))
    decoded = base64.b64decode(content.encode("ascii"), validate=False).decode("utf-8")
    return {"text": decoded, "sha": str(payload.get("sha", "")) or None}


def _github_put_file(
    target: dict[str, str],
    token: str,
    content: str,
    sha: str | None,
) -> None:
    body: dict[str, Any] = {
        "message": "Append beta tester bug report",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": target["branch"],
    }
    if sha:
        body["sha"] = sha
    request = _github_request(
        target,
        token,
        method="PUT",
        data=json.dumps(body).encode("utf-8"),
    )
    try:
        with urlopen(request, timeout=20) as response:
            response.read()
    except HTTPError as exc:
        raise ValueError(f"GitHub bug report upload failed with HTTP {exc.code}.") from exc
    except (OSError, URLError) as exc:
        raise OSError("GitHub bug report upload failed.") from exc


def _github_request(
    target: dict[str, str],
    token: str,
    *,
    method: str,
    query: str = "",
    data: bytes | None = None,
) -> Request:
    url = f"https://api.github.com/repos/{target['repo']}/contents/{target['path']}{query}"
    return Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "DnDCombatEngine-BetaReports",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


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
