from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


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

    def __init__(self, printer: Callable[[str], None] | None = None) -> None:
        self._print = printer or print
        self._root = Step(name="__root__", depth=-1)
        self._stack: List[Step] = [self._root]

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
        return False

    # Public API ---------------------------------------------------------
    def start_step(self, name: str) -> None:
        parent = self._stack[-1]
        step = Step(name=name, parent=parent, depth=len(self._stack) - 1)
        parent.children.append(step)
        self._stack.append(step)
        self._print(f"{'  ' * step.depth}▶ {name}")

    def finish_step(self, name: str) -> None:
        step = self._end_step(name)
        if step.status is StepStatus.FAILED:
            return
        step.status = StepStatus.SUCCESS
        self._print(f"{'  ' * step.depth}✔ {name}")

    def fail_step(self, name: str, error: Exception | str) -> None:
        step = self._end_step(name)
        step.status = StepStatus.FAILED
        step.error = str(error)
        self._print(f"{'  ' * step.depth}✖ {name}: {step.error}")

    def log(self, message: str) -> None:
        indent_level = max(len(self._stack) - 2, 0)
        self._print(f"{'  ' * indent_level}- {message}")

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
    def _end_step(self, name: str) -> Step:
        if len(self._stack) <= 1:
            raise RuntimeError("Cannot finish a step when no steps are active.")
        step = self._stack.pop()
        if step.name != name:
            self._stack.append(step)
            raise ValueError(f"Attempted to finish step '{name}' but current step is '{step.name}'.")
        return step
