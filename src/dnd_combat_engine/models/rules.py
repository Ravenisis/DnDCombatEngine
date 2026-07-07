"""Rule source metadata models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class RuleSource:
    """Metadata for the source of a rule-bearing game object."""

    name: str
    version: str
    license_name: str
    license_url: str
    attribution: str
    reference: str = ""

    def __post_init__(self) -> None:
        """Validate required attribution metadata."""
        if not self.name:
            raise ValueError("rule source name is required")
        if not self.version:
            raise ValueError("rule source version is required")
        if not self.license_name:
            raise ValueError("rule source license name is required")
        if not self.license_url:
            raise ValueError("rule source license URL is required")
        if not self.attribution:
            raise ValueError("rule source attribution is required")

    @classmethod
    def srd_5_2_1(cls, reference: str = "") -> Self:
        """Return metadata for the Creative Commons SRD 5.2.1 baseline."""
        return cls(
            name="System Reference Document",
            version="5.2.1",
            license_name="Creative Commons Attribution 4.0 International License",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            attribution="SRD 5.2.1 © 2024 Wizards of the Coast LLC.",
            reference=reference,
        )

    def to_dict(self) -> dict[str, str]:
        """Serialize the source metadata to JSON-compatible data."""
        return {
            "name": self.name,
            "version": self.version,
            "license_name": self.license_name,
            "license_url": self.license_url,
            "attribution": self.attribution,
            "reference": self.reference,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build rule source metadata from JSON-compatible data."""
        return cls(
            name=str(data["name"]),
            version=str(data["version"]),
            license_name=str(data["license_name"]),
            license_url=str(data["license_url"]),
            attribution=str(data["attribution"]),
            reference=str(data.get("reference", "")),
        )

