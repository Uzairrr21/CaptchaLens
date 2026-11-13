from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SolveOutcome:
    predicted_text: str | None
    confidence: float | None
    fallback_used: bool
    error_message: str | None = None


class BaseSolver(ABC):
    """Pluggable solver interface.

    Having this abstraction is what lets the tool add a fallback solver
    (e.g. a second OCR configuration, or in future a third-party API) and
    try it automatically if the primary solver's confidence is too low,
    without the caller needing to know which solver ultimately produced
    the answer.
    """

    name: str = "base"

    @abstractmethod
    def solve(self, image_bytes: bytes) -> SolveOutcome:
        raise NotImplementedError
