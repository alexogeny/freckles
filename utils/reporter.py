from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from itertools import cycle
from typing import Callable, Dict, List, Optional

from shell import nailpolish


@dataclass(frozen=True)
class Theme:
    """ANSI colour palette used by :class:`StepReporter`."""

    accent: str
    success: str
    failure: str
    log: str


@dataclass(frozen=True)
class FrecklesTheme(Theme):
    """Default Freckles palette derived from :mod:`shell.nailpolish`."""

    @classmethod
    def build(cls) -> "FrecklesTheme":
        return cls(
            accent=nailpolish.PURPLE,
            success=nailpolish.GREEN,
            failure=nailpolish.RED,
            log=nailpolish.GRAY,
        )


class StatusAnimator:
    """Render a lightweight spinner showing the current progress path."""

    _FRAMES = tuple("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    _INTERVAL = 0.1

    _GLOW_STYLES = (
        nailpolish.DIM,
        nailpolish.NORMAL,
        nailpolish.BRIGHT,
        nailpolish.NORMAL,
    )

    def __init__(self, theme: Theme, stream=None, *, pulse_enabled: bool = True) -> None:
        self._theme = theme
        self._stream = stream or sys.stdout
        self.enabled = bool(getattr(self._stream, "isatty", lambda: False)())
        self._lock = threading.Lock()
        self._status = ""
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._pulse_enabled = pulse_enabled

    def pause(self) -> None:
        if not self.enabled or self._thread is None:
            return
        self._paused.set()
        with self._lock:
            self._stream.write("\r\033[K")
            self._stream.write(nailpolish.RESET)
            self._stream.flush()

    def resume(self, status: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._status = status
        self._paused.clear()
        if self._thread is None:
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def update(self, status: str) -> None:
        if not self.enabled or self._thread is None:
            return
        with self._lock:
            self._status = status

    def stop(self, final_status: Optional[str] = None) -> None:
        if not self.enabled:
            return
        if self._thread is not None:
            self._stop.set()
            self._paused.clear()
            self._thread.join()
            self._thread = None
        with self._lock:
            self._stream.write("\r\033[K")
            self._stream.write(nailpolish.RESET)
            if final_status:
                self._stream.write(final_status)
                if not final_status.endswith("\n"):
                    self._stream.write("\n")
            self._stream.flush()

    def _run(self) -> None:
        frames = cycle(self._FRAMES)
        glow_styles = cycle(self._GLOW_STYLES) if self._pulse_enabled else None
        while not self._stop.is_set():
            if self._paused.is_set():
                time.sleep(self._INTERVAL)
                continue
            frame = next(frames)
            style = next(glow_styles) if glow_styles else ""
            with self._lock:
                self._stream.write(
                    f"\r{self._theme.accent}{frame} {style}{self._status}{nailpolish.RESET}"
                )
                self._stream.flush()
            time.sleep(self._INTERVAL)
        with self._lock:
            self._stream.write("\r\033[K")
            self._stream.write(nailpolish.RESET)
            self._stream.flush()


class StepStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Step:
    name: str
    parent: Optional["Step"] = None
    status: StepStatus = StepStatus.PENDING
    error: Optional[str] = None
    children: List["Step"] = field(default_factory=list)
    depth: int = 0
    started_at: Optional[float] = None

    def as_dict(self) -> Dict[str, Optional[str]]:
        payload: Dict[str, Optional[str]] = {
            "name": self.name,
            "status": self.status.value,
            "depth": self.depth,
            "parent": self.parent.name if self.parent else None,
        }
        if self.error:
            payload["error"] = self.error
        return payload


class StepReporter:
    """Collects hierarchical step information and renders progress messages."""

    def __init__(
        self,
        printer: Callable[[str], None] | None = None,
        theme: Theme | None = None,
        *,
        total_top_level: Optional[int] = None,
        min_step_duration: float = 0.0,
        enable_animation: bool = True,
        enable_pulse: bool = True,
    ) -> None:
        self._print = printer or print
        self._theme = theme or FrecklesTheme.build()
        self._root = Step(name="__root__", depth=-1)
        self._stack: List[Step] = [self._root]
        self._min_step_duration = max(min_step_duration, 0.0)
        self._animator = (
            None
            if printer or not enable_animation
            else StatusAnimator(self._theme, pulse_enabled=enable_pulse)
        )
        self._total_top_level = total_top_level or 0
        self._completed_top_level = 0
        self._animator_finalized = False

    def __enter__(self) -> "StepReporter":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            message = str(exc)
            while len(self._stack) > 1:
                step = self._stack.pop()
                if step.status is StepStatus.PENDING:
                    step.status = StepStatus.FAILED
                    step.error = message
        if self._animator and not self._animator_finalized:
            self._animator.stop()
        return False

    # Public API ---------------------------------------------------------
    def start_step(self, name: str) -> None:
        parent = self._stack[-1]
        step = Step(
            name=name,
            parent=parent,
            depth=len(self._stack) - 1,
            started_at=time.perf_counter(),
        )
        parent.children.append(step)
        self._stack.append(step)
        self._before_output()
        line = f"{'  ' * step.depth}▶ {name}"
        self._print(self._colorize(self._theme.accent, line))
        self._after_step_change()

    def finish_step(self, name: str) -> None:
        step = self._end_step(name)
        if step.status is StepStatus.FAILED:
            return
        step.status = StepStatus.SUCCESS
        self._ensure_min_duration(step)
        self._before_output()
        line = f"{'  ' * step.depth}✔ {name}"
        self._print(self._colorize(self._theme.success, line))
        if step.depth == 0:
            self._completed_top_level += 1
        self._after_step_change()

    def fail_step(self, name: str, error: Exception | str) -> None:
        step = self._end_step(name)
        step.status = StepStatus.FAILED
        step.error = str(error)
        self._ensure_min_duration(step)
        self._before_output()
        line = f"{'  ' * step.depth}✖ {name}: {step.error}"
        self._print(self._colorize(self._theme.failure, line))
        if self._animator:
            failure_status = f"✖ {self._format_path([s.name for s in self._stack[1:]] + [name])}"
            self._animator.stop(self._colorize(self._theme.failure, failure_status))
            self._animator_finalized = True

    def log(self, message: str) -> None:
        indent_level = max(len(self._stack) - 2, 0)
        self._before_output()
        line = f"{'  ' * indent_level}- {message}"
        self._print(self._colorize(self._theme.log, line))
        self._after_step_change()

    def summary(self) -> Dict[str, List[Dict[str, Optional[str]]]]:
        succeeded: List[Dict[str, Optional[str]]] = []
        failed: List[Dict[str, Optional[str]]] = []

        def visit(step: Step) -> None:
            for child in step.children:
                if child.status is StepStatus.SUCCESS:
                    succeeded.append(child.as_dict())
                elif child.status is StepStatus.FAILED:
                    failed.append(child.as_dict())
                visit(child)

        visit(self._root)
        return {"succeeded": succeeded, "failed": failed}

    # Internal helpers ---------------------------------------------------
    def _before_output(self) -> None:
        if self._animator:
            self._animator.pause()

    @staticmethod
    def _colorize(colour: str, message: str) -> str:
        if not colour:
            return message
        return f"{colour}{message}{nailpolish.RESET}"

    def _after_step_change(self) -> None:
        if not self._animator:
            return
        status = self._current_status()
        if status:
            self._animator.resume(status)
        elif len(self._stack) <= 1:
            if self._total_top_level and self._completed_top_level >= self._total_top_level:
                final = f"✔ [{self._total_top_level}/{self._total_top_level}] All phases complete"
                self._animator.stop(self._colorize(self._theme.success, final))
                self._animator_finalized = True
            elif self._completed_top_level:
                self._animator.stop(
                    self._colorize(self._theme.success, "✔ All phases complete")
                )
                self._animator_finalized = True
            else:
                self._animator.pause()
        else:
            self._animator.pause()

    def _current_status(self) -> str:
        if len(self._stack) <= 1:
            return ""
        path = [step.name for step in self._stack[1:]]
        prefix = ""
        if self._total_top_level:
            current_index = min(self._completed_top_level + 1, self._total_top_level)
            prefix = f"[{current_index}/{self._total_top_level}] "
        return prefix + self._format_path(path)

    @staticmethod
    def _format_path(path: List[str]) -> str:
        return " › ".join(path)

    def _end_step(self, name: str) -> Step:
        if len(self._stack) <= 1:
            raise RuntimeError("Cannot finish a step when no steps are active.")
        step = self._stack.pop()
        if step.name != name:
            self._stack.append(step)
            raise ValueError(f"Attempted to finish step '{name}' but current step is '{step.name}'.")
        return step

    def _ensure_min_duration(self, step: Step) -> None:
        if self._min_step_duration <= 0 or step.started_at is None:
            return
        elapsed = time.perf_counter() - step.started_at
        remaining = self._min_step_duration - elapsed
        if remaining > 0:
            time.sleep(remaining)
