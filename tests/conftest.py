"""Shared pytest fixtures for the test suite."""

from collections.abc import Callable
from dataclasses import dataclass, field

import pytest


@dataclass
class FakeTimer:
    """A scheduled callback captured by :class:`FakeScheduler`."""

    at: float
    callback: Callable[[], None]
    cancelled: bool = False
    fired: bool = False

    def cancel(self) -> None:
        self.cancelled = True


@dataclass
class FakeScheduler:
    """Deterministic replacement for the asyncio-based timer scheduler.

    Records scheduled callbacks and fires them (in due order) only when the
    virtual clock is advanced with :meth:`advance`.
    """

    now: float = 0.0
    timers: list[FakeTimer] = field(default_factory=list)

    def __call__(self, delay_ms: float, callback: Callable[[], None]) -> Callable[[], None]:
        timer = FakeTimer(at=self.now + delay_ms, callback=callback)
        self.timers.append(timer)
        return timer.cancel

    def advance(self, ms: float) -> None:
        """Advance the virtual clock, firing due callbacks in order."""
        end = self.now + ms
        while True:
            due = [t for t in self.timers if not t.cancelled and not t.fired and t.at <= end]
            if not due:
                break
            timer = min(due, key=lambda t: t.at)
            self.now = timer.at
            timer.fired = True
            timer.callback()
        self.now = end

    @property
    def pending(self) -> list[FakeTimer]:
        """Return timers that are still scheduled (not fired, not cancelled)."""
        return [t for t in self.timers if not t.cancelled and not t.fired]


@pytest.fixture
def scheduler() -> FakeScheduler:
    """Provide a fresh deterministic scheduler."""
    return FakeScheduler()
