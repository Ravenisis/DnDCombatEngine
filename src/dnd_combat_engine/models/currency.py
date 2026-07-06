"""Currency purse model."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self

COPPER_PER_SP = 10
COPPER_PER_GP = 100
COPPER_PER_PP = 1000


@dataclass(frozen=True, slots=True)
class CurrencyPurse:
    """A D&D coin purse stored in normalized denominations."""

    pp: int = 0
    gp: int = 0
    sp: int = 0
    cp: int = 0

    def __post_init__(self) -> None:
        """Validate coin counts."""
        for name, value in self.to_dict().items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

    @property
    def total_cp(self) -> int:
        """Return the purse value in copper pieces."""
        return (
            self.pp * COPPER_PER_PP
            + self.gp * COPPER_PER_GP
            + self.sp * COPPER_PER_SP
            + self.cp
        )

    def add_cp(self, amount_cp: int) -> Self:
        """Return a normalized purse with copper added or removed."""
        total = self.total_cp + amount_cp
        if total < 0:
            raise ValueError("currency cannot be negative")
        return type(self).from_cp(total)

    def to_dict(self) -> dict[str, int]:
        """Serialize the purse to plain JSON-compatible data."""
        return {"pp": self.pp, "gp": self.gp, "sp": self.sp, "cp": self.cp}

    @classmethod
    def from_cp(cls, amount_cp: int) -> Self:
        """Create the simplest PP/GP/SP/CP representation for copper."""
        if amount_cp < 0:
            raise ValueError("amount_cp cannot be negative")
        pp, remainder = divmod(amount_cp, COPPER_PER_PP)
        gp, remainder = divmod(remainder, COPPER_PER_GP)
        sp, cp = divmod(remainder, COPPER_PER_SP)
        return cls(pp=pp, gp=gp, sp=sp, cp=cp)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a purse from JSON-compatible data."""
        return cls.from_cp(
            int(data.get("pp", 0)) * COPPER_PER_PP
            + int(data.get("gp", 0)) * COPPER_PER_GP
            + int(data.get("sp", 0)) * COPPER_PER_SP
            + int(data.get("cp", 0))
        )

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse text such as '1PP 100GP' into a normalized purse."""
        matches = tuple(re.finditer(r"(\d+)\s*(pp|gp|sp|cp)", text.lower()))
        if not matches:
            raise ValueError("enter currency like 1PP 100GP 5SP")
        consumed = "".join(match.group(0) for match in matches)
        compact = re.sub(r"\s+", "", text.lower())
        if consumed.replace(" ", "") != compact:
            raise ValueError("currency can only include PP, GP, SP, and CP amounts")
        total = 0
        for match in matches:
            amount = int(match.group(1))
            denomination = match.group(2)
            total += amount * {
                "pp": COPPER_PER_PP,
                "gp": COPPER_PER_GP,
                "sp": COPPER_PER_SP,
                "cp": 1,
            }[denomination]
        return cls.from_cp(total)
