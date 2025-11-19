from __future__ import annotations

import builtins
import sys
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from itertools import cycle
from typing import Callable, Deque, Dict, List, Optional, Tuple

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


@dataclass(frozen=True)
class StatusMessage:
    prefix: str
    segments: Tuple[str, ...]
    raw: str


class StatusAnimator:
    """Render a lightweight spinner showing the current progress path."""

    _FRAMES = tuple("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    _INTERVAL = 0.1

    _PULSE_WAVE = (
        nailpolish.DIM,
        nailpolish.DIM,
        nailpolish.NORMAL,
        nailpolish.BRIGHT,
        nailpolish.BRIGHT,
        nailpolish.NORMAL,
        nailpolish.DIM,
        nailpolish.DIM,
    )

    _GLOW_HOLD_TICKS = 3

    def __init__(self, theme: Theme, stream=None, *, pulse_enabled: bool = True) -> None:
        self._theme = theme
        self._stream = stream or sys.stdout
        self.enabled = bool(getattr(self._stream, "isatty", lambda: False)())
        self._lock = threading.Lock()
        self._status: Optional[StatusMessage] = None
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._pulse_enabled = pulse_enabled
        self._glow_index = 0
        self._glow_tick = 0
        self._pulse_phase = 0

    def pause(self) -> None:
        if not self.enabled or self._thread is None:
            return
        self._paused.set()
        with self._lock:
            self._stream.write("\r\033[K")
            self._stream.write(nailpolish.RESET)
            self._stream.flush()

    def resume(self, status: StatusMessage) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._status = status
            self._glow_index = 0
            self._glow_tick = 0
            self._pulse_phase = 0
        self._paused.clear()
        if self._thread is None:
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def update(self, status: StatusMessage) -> None:
        if not self.enabled or self._thread is None:
            return
        with self._lock:
            self._status = status
            self._glow_index = 0
            self._glow_tick = 0
            self._pulse_phase = 0

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
        while not self._stop.is_set():
            if self._paused.is_set():
                time.sleep(self._INTERVAL)
                continue
            frame = next(frames)
            with self._lock:
                self._stream.write("\r\033[K")
                self._stream.write(
                    f"{self._theme.accent}{frame}{nailpolish.RESET} {self._render_status()}"
                )
                self._stream.flush()
            self._advance_glow()
            time.sleep(self._INTERVAL)
        with self._lock:
            self._stream.write("\r\033[K")
            self._stream.write(nailpolish.RESET)
            self._stream.flush()

    def _render_status(self) -> str:
        status = self._status
        if status is None:
            return ""
        if not self._pulse_enabled or not status.segments:
            return status.raw
        segment_count = len(status.segments)
        if segment_count == 1:
            segment = self._pulse_segment(status.segments[0])
            return f"{status.prefix}{segment}"
        parts: List[str] = []
        for index, segment in enumerate(status.segments):
            distance = (index - self._glow_index) % segment_count
            if distance == 0:
                parts.append(self._pulse_segment(segment))
            elif distance == 1 or distance == segment_count - 1:
                parts.append(self._wrap_segment(segment, nailpolish.NORMAL))
            else:
                parts.append(self._wrap_segment(segment, nailpolish.DIM))
        return f"{status.prefix}{' › '.join(parts)}"

    def _pulse_segment(self, segment: str) -> str:
        if not segment:
            return segment
        pieces: List[str] = [self._theme.accent]
        wave = StatusAnimator._PULSE_WAVE
        wave_length = len(wave)
        for offset, char in enumerate(segment):
            pieces.append(wave[(self._pulse_phase + offset) % wave_length])
            pieces.append(char)
        pieces.append(nailpolish.RESET)
        return "".join(pieces)

    def _wrap_segment(self, segment: str, intensity: str) -> str:
        if not segment:
            return segment
        return "".join((self._theme.accent, intensity, segment, nailpolish.RESET))

    def _advance_glow(self) -> None:
        if not self._pulse_enabled or self._status is None:
            return
        self._pulse_phase = (self._pulse_phase + 1) % len(StatusAnimator._PULSE_WAVE)
        segment_count = len(self._status.segments)
        if segment_count == 0:
            return
        if segment_count > 1:
            self._glow_tick += 1
            if self._glow_tick >= StatusAnimator._GLOW_HOLD_TICKS:
                self._glow_tick = 0
                self._glow_index = (self._glow_index + 1) % segment_count


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
        self._structured_display = bool(
            printer is None and getattr(sys.stdout, "isatty", lambda: False)()
        )
        self._use_alt_screen = self._structured_display
        animation_enabled = (
            not self._structured_display and printer is None and enable_animation
        )
        self._animator = (
            None
            if not animation_enabled
            else StatusAnimator(self._theme, pulse_enabled=enable_pulse)
        )
        self._total_top_level = total_top_level or 0
        self._completed_top_level = 0
        self._animator_finalized = False
        self._input_patch_depth = 0
        self._original_input: Optional[Callable[[str], str]] = None
        self._log_buffer: Deque[Tuple[Tuple[str, ...], str]] = deque(maxlen=200)
        self._log_window = 40
        self._scene_active = False

    def __enter__(self) -> "StepReporter":
        if self._structured_display:
            self._activate_scene()
            self._render_scene()
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
            self._finalize_animation()
        if self._structured_display and self._scene_active:
            message = self._final_scene_line(success=exc_type is None)
            self._deactivate_scene(message)
        return False

    @property
    def needs_final_summary(self) -> bool:
        return not self._structured_display

    def _activate_scene(self) -> None:
        if not self._use_alt_screen or self._scene_active:
            return
        sys.stdout.write("\033[?1049h\033[?25l")
        sys.stdout.flush()
        self._scene_active = True

    def _deactivate_scene(self, final_message: Optional[str]) -> None:
        if not self._scene_active:
            return
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
        self._scene_active = False
        if final_message:
            self._print(final_message)

    def _final_scene_line(self, *, success: bool) -> Optional[str]:
        if success and all(child.status is StepStatus.SUCCESS for child in self._root.children):
            return self._colorize(self._theme.success, "✔ Freckles setup complete")
        if success:
            return self._colorize(self._theme.log, "⚠ Freckles setup finished with partial progress")
        return self._colorize(self._theme.failure, "✖ Freckles setup interrupted")

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
        animator_enabled = bool(getattr(self._animator, "enabled", False)) if self._animator else False
        if not animator_enabled:
            self._before_output()
            self._emit_story_line("▶", name, step.depth, self._theme.accent)
        self._after_step_change()

    def finish_step(self, name: str) -> None:
        step = self._end_step(name)
        if step.status is StepStatus.FAILED:
            return
        step.status = StepStatus.SUCCESS
        self._ensure_min_duration(step)
        self._before_output()
        self._emit_story_line("✔", name, step.depth, self._theme.success)
        if step.depth == 0:
            self._completed_top_level += 1
        self._after_step_change()

    def fail_step(self, name: str, error: Exception | str) -> None:
        step = self._end_step(name)
        step.status = StepStatus.FAILED
        step.error = str(error)
        self._ensure_min_duration(step)
        self._before_output()
        message = f"{name}: {step.error}"
        self._emit_story_line("✖", message, step.depth, self._theme.failure)
        if self._animator:
            failure_status = f"✖ {self._format_path([s.name for s in self._stack[1:]] + [name])}"
            self._animator.stop(self._colorize(self._theme.failure, failure_status))
            self._animator_finalized = True

    def log(self, message: str) -> None:
        indent_level = max(len(self._stack) - 2, 0)
        self._before_output()
        self._emit_story_line("•", message, indent_level, self._theme.log)
        self._after_step_change()

    @contextmanager
    def interactive_section(self):
        """Temporarily pause the status animation for interactive prompts."""

        with self._patched_input():
            if not self._animator or self._animator_finalized:
                yield
                return

            self._animator.pause()
            try:
                yield
            except Exception:
                if self._animator and not self._animator_finalized:
                    self._animator.pause()
                raise
            else:
                if self._animator and not self._animator_finalized:
                    status = self._current_status()
                    if status is not None:
                        self._animator.resume(status)
                    else:
                        self._animator.pause()

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

    def _emit_story_line(self, icon: str, message: str, depth: int, colour: str) -> None:
        line = self._format_story_line(icon, message, depth)
        colored = self._colorize(colour, line)
        if not self._structured_display:
            self._print(colored)
            return
        if icon in {"•", "?"}:
            self._log_buffer.append((self._active_path(), colored))
        self._render_scene()

    @staticmethod
    def _format_story_line(icon: str, message: str, depth: int) -> str:
        indent = "  " * depth
        return f"{indent}{icon} {message}"

    def _active_path(self) -> Tuple[str, ...]:
        return tuple(step.name for step in self._stack[1:])

    def _render_scene(self) -> None:
        if not self._structured_display:
            return
        board_lines = self._build_board_lines()
        active_path = self._active_path()
        if not active_path:
            log_lines: List[str] = []
        else:
            scoped = [line for path, line in self._log_buffer if path == active_path]
            log_lines = scoped[-self._log_window :]
        output: List[str] = ["\033[H\033[J"]
        output.extend(board_lines)
        output.append("")
        if log_lines:
            output.extend(log_lines)
        else:
            if active_path:
                path_text = " › ".join(active_path)
                placeholder = self._colorize(self._theme.log, f"Working on {path_text}…")
            else:
                placeholder = self._colorize(self._theme.log, "Awaiting next step…")
            output.append(placeholder)
        scene = "\n".join(output)
        sys.stdout.write(scene)
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _build_board_lines(self) -> List[str]:
        lines: List[str] = []
        progress = ""
        if self._total_top_level:
            progress = f"[{self._completed_top_level}/{self._total_top_level}] "
        lines.append(self._colorize(self._theme.accent, f"{progress}Freckles setup checklist"))
        if not self._root.children:
            lines.append(self._colorize(self._theme.log, "Waiting for phases to start…"))
            return lines
        for child in self._root.children:
            lines.append(self._format_board_entry(child))
        return lines

    def _format_board_entry(self, step: Step) -> str:
        if any(active is step for active in self._stack[1:]):
            icon = "▸"
            colour = self._theme.accent
        elif step.status is StepStatus.SUCCESS:
            icon = "✔"
            colour = self._theme.success
        elif step.status is StepStatus.FAILED:
            icon = "✖"
            colour = self._theme.failure
        else:
            icon = "○"
            colour = self._theme.log
        return self._colorize(colour, f"{icon} {step.name}")

    def _after_step_change(self) -> None:
        if not self._animator:
            return
        status = self._current_status()
        if status is not None:
            self._animator.resume(status)
        elif len(self._stack) <= 1:
            if self._total_top_level and self._completed_top_level >= self._total_top_level:
                self._finalize_animation()
            else:
                self._animator.pause()
        else:
            self._animator.pause()

    def _current_status(self) -> Optional[StatusMessage]:
        if len(self._stack) <= 1:
            return None
        path = [step.name for step in self._stack[1:]]
        prefix = ""
        if self._total_top_level:
            current_index = min(self._completed_top_level + 1, self._total_top_level)
            prefix = f"[{current_index}/{self._total_top_level}] "
        formatted_path = self._format_path(path)
        return StatusMessage(prefix=prefix, segments=tuple(path), raw=f"{prefix}{formatted_path}")

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

    def _finalize_animation(self) -> None:
        if not self._animator or self._animator_finalized:
            return
        final_status = self._final_status_message()
        self._animator.stop(final_status)
        self._animator_finalized = True

    def _final_status_message(self) -> Optional[str]:
        if not self._animator:
            return None
        if self._total_top_level:
            if self._completed_top_level >= self._total_top_level:
                final = f"✔ [{self._total_top_level}/{self._total_top_level}] All phases complete"
                return self._colorize(self._theme.success, final)
            return None
        if self._completed_top_level:
            return self._colorize(self._theme.success, "✔ All phases complete")
        return None

    @contextmanager
    def _patched_input(self):
        if self._input_patch_depth == 0:
            self._original_input = builtins.input

            def prompt_input(message: object = "") -> str:
                return self._handle_prompt_input(message)

            builtins.input = prompt_input  # type: ignore[assignment]
        self._input_patch_depth += 1
        try:
            yield
        finally:
            self._input_patch_depth -= 1
            if self._input_patch_depth == 0 and self._original_input is not None:
                builtins.input = self._original_input  # type: ignore[assignment]
                self._original_input = None

    def _handle_prompt_input(self, message: object) -> str:
        text = str(message).rstrip()
        if text:
            indent_level = max(len(self._stack) - 2, 0)
            self._before_output()
            self._emit_story_line("?", text, indent_level, self._theme.accent)
        if self._original_input is None:
            raise RuntimeError("Interactive prompt invoked outside managed context.")
        return self._original_input("> ")
