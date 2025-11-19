from __future__ import annotations

from queue import Queue
from typing import List

import shell.loader as loader


class FakeWriter(loader.TerminalWriter):
    def __init__(self) -> None:
        self.output: List[str] = []
        super().__init__(self.output.append, lambda: None)

    def dump(self) -> str:
        return "".join(self.output)


def test_render_completion_reports_status(monkeypatch):
    writer = FakeWriter()
    spinner = loader.SpinnerDisplay(message="Build assets", command=["true"], writer=writer)
    spinner._render_completion(0)
    assert "Build assets ... OK" in writer.dump()


def test_drain_queue_caps_history():
    writer = FakeWriter()
    spinner = loader.SpinnerDisplay(message="Hi", command=["true"], writer=writer)
    queue: Queue[str] = Queue()
    for item in ["one", "two", "three"]:
        queue.put(item)
    buffer: List[str] = []
    spinner._drain_queue(queue, buffer, max_lines=2)
    assert buffer == ["two", "three"]


def test_render_frame_uses_spinner(monkeypatch):
    writer = FakeWriter()
    spinner = loader.SpinnerDisplay(message="Run task", command=["true"], writer=writer)

    calls: List[int] = []

    def fake_clear(lines: int) -> None:
        calls.append(lines)

    monkeypatch.setattr(loader, "clear_previous_lines", fake_clear)
    spinner._render_frame(["hello"], width=10, spinner_index=3)
    assert calls == [3]
    assert loader.BRAILLE_SPINNER[3] in writer.dump()
