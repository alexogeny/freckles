from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from utils.reporter import StepReporter


@dataclass(frozen=True)
class Phase:
    """Represents a provisioning phase surfaced to the StepReporter."""

    name: str
    handler: Callable[[StepReporter], None]

