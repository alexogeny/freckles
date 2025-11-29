from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def step(reporter, name: str):
    """Lightweight context manager to wrap a reporter step."""
    reporter.start_step(name)
    try:
        yield
    except Exception as exc:  # pragma: no cover - propagates to caller
        reporter.fail_step(name, exc)
        raise
    else:
        reporter.finish_step(name)
