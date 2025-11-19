"""Animated spinner wrapper used when provisioning long-running commands."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Thread
from typing import Callable, List, Sequence, Tuple

from nailpolish import BLUE, GRAY, GREEN, RED, RESET

BRAILLE_SPINNER: Tuple[str, ...] = tuple("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
ERASE_LINE = "\033[K"
CURSOR_UP = "\033[1A"


class TerminalWriter:
    """Minimal abstraction for writing terminal output.

    A dedicated writer makes :class:`SpinnerDisplay` easier to test without
    touching the actual stdout stream.
    """

    def __init__(self, write: Callable[[str], None] | None = None, flush: Callable[[], None] | None = None):
        self._write = write or sys.stdout.write
        self._flush = flush or sys.stdout.flush

    def write(self, text: str) -> None:
        self._write(text)

    def writeln(self, text: str = "") -> None:
        self._write(f"{text}\n")

    def flush(self) -> None:
        self._flush()


def terminal_dimensions() -> Tuple[int, int]:
    """Return (width, height) using sensible fallbacks."""
    size = shutil.get_terminal_size((80, 24))
    return size.columns, size.lines


def clear_previous_lines(line_count: int) -> None:
    """Move the cursor up ``line_count`` rows and clear each line."""
    for _ in range(max(line_count, 0)):
        sys.stdout.write(f"{CURSOR_UP}{ERASE_LINE}")


def enqueue_output(stream, queue: Queue[str]) -> None:
    """Feed each stdout/stderr line into a queue for async consumption."""
    for line in iter(stream.readline, ""):
        queue.put(line.rstrip("\n"))
    stream.close()


@dataclass
class SpinnerDisplay:
    message: str
    command: Sequence[str]
    refresh_interval: float = 0.1
    writer: TerminalWriter = TerminalWriter()

    def run(self) -> int:
        width, height = terminal_dimensions()
        max_lines = max(height - 3, 1)
        buffer: List[str] = []
        queue: Queue[str] = Queue()
        spinner_index = 0

        process = subprocess.Popen(  # noqa: PLW1510 - intentional background process
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        assert process.stdout is not None  # appease type-checkers

        reader = Thread(target=enqueue_output, args=(process.stdout, queue), daemon=True)
        reader.start()

        try:
            while process.poll() is None:
                self._drain_queue(queue, buffer, max_lines)
                self._render_frame(buffer, width, spinner_index)
                spinner_index = (spinner_index + 1) % len(BRAILLE_SPINNER)
                time.sleep(self.refresh_interval)
            # Flush any trailing lines after process completion.
            self._drain_queue(queue, buffer, max_lines)
            self._render_completion(process.returncode or 0)
            return process.returncode or 0
        except KeyboardInterrupt:
            process.terminate()
            self.writer.writeln("\nProcess interrupted by user.")
            return 1

    def _drain_queue(self, queue: Queue[str], buffer: List[str], max_lines: int) -> None:
        while True:
            try:
                line = queue.get_nowait()
            except Empty:
                break
            buffer.append(line)
            if len(buffer) > max_lines:
                del buffer[0]

    def _render_frame(self, buffer: Sequence[str], width: int, spinner_index: int) -> None:
        clear_previous_lines(len(buffer) + 2)
        self.writer.writeln(f"{BLUE}{self.message}{RESET}")
        self.writer.write(f"{BRAILLE_SPINNER[spinner_index]}")
        self.writer.flush()
        for line in buffer:
            trimmed = line[: max(width - 1, 1)]
            self.writer.write(f"\n{GRAY}{trimmed}{RESET}")

    def _render_completion(self, exit_code: int) -> None:
        self.writer.write("\r")
        self.writer.flush()
        status = "OK" if exit_code == 0 else f"NOT OK ({exit_code})"
        colour = GREEN if exit_code == 0 else RED
        self.writer.writeln(f"{colour}{self.message} ... {status}{RESET}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show a spinner for a command.")
    parser.add_argument("message", help="Status text to display above the spinner.")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute (specify after -- if invoking via python).",
    )
    args = parser.parse_args()
    if not args.command:
        parser.error("No command provided.")
    return args


def main() -> None:
    args = parse_args()
    spinner = SpinnerDisplay(message=args.message, command=args.command)
    sys.exit(spinner.run())


if __name__ == "__main__":
    main()
