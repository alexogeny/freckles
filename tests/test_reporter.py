from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.reporter import StepReporter


class _DummyAnimator:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, Optional[str]]] = []

    def pause(self) -> None:
        self.calls.append(("pause", None))

    def resume(self, status: str) -> None:
        self.calls.append(("resume", status))

    def stop(self, final_status: Optional[str] = None) -> None:
        self.calls.append(("stop", final_status))


def test_interactive_section_pauses_and_resumes() -> None:
    outputs: List[str] = []
    reporter = StepReporter(printer=outputs.append)
    reporter._animator = _DummyAnimator()

    with reporter:
        reporter.start_step("phase")
        reporter._animator.calls.clear()

        with reporter.interactive_section():
            pass

        assert reporter._animator.calls[0] == ("pause", None)
        assert reporter._animator.calls[1][0] == "resume"
        assert reporter._animator.calls[1][1]

        reporter.finish_step("phase")


def test_final_message_emitted_once_without_total() -> None:
    outputs: List[str] = []
    reporter = StepReporter(printer=outputs.append)
    reporter._animator = _DummyAnimator()

    with reporter:
        reporter.start_step("phase")
        reporter.finish_step("phase")

        stop_calls = [call for call in reporter._animator.calls if call[0] == "stop"]
        assert not stop_calls
        assert reporter._animator_finalized is False

    stop_calls = [call for call in reporter._animator.calls if call[0] == "stop"]
    assert len(stop_calls) == 1
    assert "All phases complete" in (stop_calls[0][1] or "")
    assert reporter._animator_finalized is True


def test_final_message_emitted_when_total_complete() -> None:
    outputs: List[str] = []
    reporter = StepReporter(printer=outputs.append, total_top_level=1)
    reporter._animator = _DummyAnimator()

    with reporter:
        reporter.start_step("phase")
        reporter.finish_step("phase")

        stop_calls = [call for call in reporter._animator.calls if call[0] == "stop"]
        assert len(stop_calls) == 1
        assert "[1/1]" in (stop_calls[0][1] or "")
        assert reporter._animator_finalized is True

    stop_calls = [call for call in reporter._animator.calls if call[0] == "stop"]
    assert len(stop_calls) == 1
