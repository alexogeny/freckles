from __future__ import annotations

import argparse
import sys

from freckles.application.provisioning_runner import execute_phases
from freckles.domain.provisioning import Phase
from freckles.infrastructure.command import configure_runner
from utils.reporter import StepReporter

import setup as legacy_setup


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision a Freckles workstation.")
    parser.add_argument(
        "--noop",
        action="store_true",
        help="Log actions without executing shell commands.",
    )
    return parser.parse_args(argv)


def build_phases() -> list[Phase]:
    """Reuse the phase definitions from the legacy setup module."""
    return legacy_setup.build_phases()


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    mode = "noop" if args.noop else "real"
    configure_runner(mode)

    if not legacy_setup.is_debian_like():
        sys.exit("Freckles currently supports Debian and Ubuntu systems only.")

    phases = build_phases()
    reporter = StepReporter(
        total_top_level=len(phases),
        min_step_duration=0.35,
        enable_animation=True,
        enable_pulse=True,
    )
    try:
        with reporter:
            execute_phases(phases, reporter)
    except Exception:
        if reporter.needs_final_summary:
            legacy_setup.emit_summary(reporter.summary())
        raise
    else:
        if reporter.needs_final_summary:
            legacy_setup.emit_summary(reporter.summary())


if __name__ == "__main__":
    main()
