from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_srd_third_party_license_is_vendored() -> None:
    text = (ROOT / "THIRD_PARTY_LICENSES" / "SRD.md").read_text(encoding="utf-8")

    assert "System Reference Document 5.2.1" in text
    assert "Creative Commons Attribution 4.0 International License" in text
    assert "https://creativecommons.org/licenses/by/4.0/" in text


def test_repo_facing_docs_do_not_reference_personal_srd_paths() -> None:
    checked_paths = [
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "DEVNOTES.md",
        ROOT / "docs",
        ROOT / "THIRD_PARTY_LICENSES",
    ]
    forbidden_fragments = (
        "C:" + "\\Users\\",
        "Downloads" + "\\dnd-5e-srd",
        "dnd-5e-srd" + "-markdown-master",
    )
    text_files: list[Path] = []
    for checked_path in checked_paths:
        if checked_path.is_file():
            text_files.append(checked_path)
        elif checked_path.exists():
            text_files.extend(checked_path.rglob("*.md"))

    offenders = [
        str(path.relative_to(ROOT))
        for path in text_files
        if any(
            fragment in path.read_text(encoding="utf-8")
            for fragment in forbidden_fragments
        )
    ]

    assert offenders == []
