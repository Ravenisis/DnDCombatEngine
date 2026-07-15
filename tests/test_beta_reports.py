from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from dnd_combat_engine.controllers import BetaReportController
from dnd_combat_engine.models import BetaBugReport
from dnd_combat_engine.services import BetaReportService, beta_report_service
from dnd_combat_engine.services import token_store as token_store_module
from dnd_combat_engine.services.token_store import UserTokenStore


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


def test_beta_report_service_uses_and_manages_saved_token(monkeypatch, tmp_path) -> None:
    class TokenStore:
        token = None

        def load(self):
            return self.token

        def save(self, token):
            self.token = token

        def clear(self):
            self.token = None

    store = TokenStore()
    service = BetaReportService(store)
    monkeypatch.delenv("DND_COMBAT_ENGINE_GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(service, "submit_report_to_github", lambda report, token: token)

    assert service.github_upload_configured is False
    service.configure_github_token("saved-token")
    assert service.github_upload_configured is True
    assert service.submit_report(tmp_path / "unused.md", BetaBugReport("Bug", "Details")) == (
        "saved-token"
    )
    service.clear_github_token()
    assert service.github_upload_configured is False


def test_user_token_store_encrypts_round_trip_and_clears(monkeypatch, tmp_path) -> None:
    store = UserTokenStore(tmp_path / "settings" / "token.bin")
    monkeypatch.setattr(token_store_module.os, "name", "nt")
    monkeypatch.setattr(token_store_module, "_protect_data", lambda value: value[::-1])
    monkeypatch.setattr(token_store_module, "_unprotect_data", lambda value: value[::-1])

    assert store.load() is None
    store.save("  secret-token  ")
    assert b"secret-token" not in store.path.read_bytes()
    assert store.load() == "secret-token"
    store.clear()
    assert store.load() is None


def test_user_token_store_rejects_invalid_or_insecure_storage(monkeypatch, tmp_path) -> None:
    store = UserTokenStore(tmp_path / "token.bin")
    with pytest.raises(ValueError, match="empty"):
        store.save(" ")
    monkeypatch.setattr(token_store_module.os, "name", "posix")
    with pytest.raises(OSError, match="only on Windows"):
        store.save("token")
    store.path.write_bytes(b"unknown")
    with pytest.raises(OSError, match="unsupported format"):
        store.load()
    store.path.write_bytes(token_store_module._DPAPI_HEADER + b"encrypted")  # noqa: SLF001
    with pytest.raises(OSError, match="only be decrypted on Windows"):
        store.load()


def test_dpapi_bindings_protect_and_unprotect(monkeypatch) -> None:
    class Crypt32:
        def __init__(self) -> None:
            self.buffers = []

        def transform(self, source_pointer, output_pointer) -> int:
            source = token_store_module.ctypes.cast(
                source_pointer,
                token_store_module.ctypes.POINTER(token_store_module._DataBlob),  # noqa: SLF001
            ).contents
            value = token_store_module.ctypes.string_at(source.data, source.size)[::-1]
            buffer = token_store_module.ctypes.create_string_buffer(value)
            self.buffers.append(buffer)
            output = token_store_module.ctypes.cast(
                output_pointer,
                token_store_module.ctypes.POINTER(token_store_module._DataBlob),  # noqa: SLF001
            ).contents
            output.size = len(value)
            output.data = token_store_module.ctypes.cast(
                buffer,
                token_store_module.ctypes.POINTER(token_store_module.ctypes.c_char),
            )
            return 1

        def CryptProtectData(self, source, *args):  # noqa: N802
            return self.transform(source, args[-1])

        def CryptUnprotectData(self, source, *args):  # noqa: N802
            return self.transform(source, args[-1])

    crypt32 = Crypt32()
    kernel32 = SimpleNamespace(LocalFree=lambda pointer: None)
    monkeypatch.setattr(
        token_store_module.ctypes,
        "windll",
        SimpleNamespace(crypt32=crypt32, kernel32=kernel32),
        raising=False,
    )

    encrypted = token_store_module._protect_data(b"secret")  # noqa: SLF001

    assert encrypted == b"terces"
    assert token_store_module._unprotect_data(encrypted) == b"secret"  # noqa: SLF001


def test_beta_report_controller_manages_github_token(tmp_path) -> None:
    class Store:
        token = None

        def load(self):
            return self.token

        def save(self, token):
            self.token = token

        def clear(self):
            self.token = None

    controller = BetaReportController(BetaReportService(Store()), tmp_path / "reports.md")

    controller.configure_github_token("token")
    assert controller.github_upload_configured is True
    controller.clear_github_token()
    assert controller.github_upload_configured is False


def test_beta_bug_report_requires_summary_and_description() -> None:
    with pytest.raises(ValueError, match="summary"):
        BetaBugReport("", "Description")
    with pytest.raises(ValueError, match="description"):
        BetaBugReport("Summary", "")
