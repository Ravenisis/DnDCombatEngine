import re

from dnd_combat_engine import __version__
from dnd_combat_engine.version import (
    APP_VERSION,
    VERSION_LAST_MODIFIED_EASTERN,
    about_text,
)


def test_version_metadata_is_consistent_and_user_facing() -> None:
    assert __version__ == APP_VERSION
    assert re.fullmatch(r"1\.\d+\.\d+", APP_VERSION)
    assert re.fullmatch(
        r"\d{2}/\d{2}/\d{4} \d{2}:\d{2} (?:am|pm)",
        VERSION_LAST_MODIFIED_EASTERN,
    )
    assert f"DnDCombatEngine {APP_VERSION}" in about_text()
    assert VERSION_LAST_MODIFIED_EASTERN in about_text()
