from __future__ import annotations

from typing import Iterable

from freckles.domain.provisioning import Phase
from utils.reporter import StepReporter


def execute_phases(phases: Iterable[Phase], reporter: StepReporter) -> None:
    """Run provisioning phases with reporting."""
    for phase in phases:
        reporter.start_step(phase.name)
        try:
            phase.handler(reporter)
        except Exception as exc:  # pragma: no cover - propagation for summary
            reporter.fail_step(phase.name, exc)
            raise
        else:
            reporter.finish_step(phase.name)
