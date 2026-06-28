"""UI-friendly controller error helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ControllerError:
    """A UI-friendly error description."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ControllerResult(Generic[T]):
    """A success-or-error result for UI command handlers."""

    value: T | None = None
    error: ControllerError | None = None

    @property
    def ok(self) -> bool:
        """Return whether the command succeeded."""
        return self.error is None


def capture_controller_error(action: Callable[[], T]) -> ControllerResult[T]:
    """Run an action and convert common exceptions into controller errors."""
    try:
        return ControllerResult(value=action())
    except ValueError as exc:
        return ControllerResult(error=ControllerError("validation_error", str(exc)))
    except KeyError as exc:
        return ControllerResult(error=ControllerError("not_found", str(exc)))

