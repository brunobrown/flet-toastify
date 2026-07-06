"""Observable toast state, fully testable without a UI.

:class:`Toasts` owns the list of active :class:`~flet_toastify.models.Toast`
objects and orchestrates their lifecycle (``ENTERING`` → ``VISIBLE`` →
``LEAVING`` → removed) with cancellable timers. Because the class is
decorated with ``@ft.observable``, every mutation of the public
:attr:`Toasts.toasts` list notifies subscribed components and triggers a
re-render — no manual ``update()`` calls anywhere.

The module also exposes :data:`toast`, the default :class:`Toasts` instance
behind the package-level global API (``toast.success("saved!")``), following
the pattern of react-toastify and sonner.
"""

import asyncio
from collections.abc import Callable

import flet as ft

from flet_toastify.models import DEFAULT_DURATION_MS, Toast
from flet_toastify.style import ToastStyle
from flet_toastify.types import ToastPhase, ToastType

__all__ = ["Scheduler", "Toasts", "toast"]

type CancelTimer = Callable[[], None]
"""Cancels a previously scheduled callback."""

type Scheduler = Callable[[float, Callable[[], None]], CancelTimer]
"""Schedules ``callback`` after ``delay_ms`` milliseconds; returns a canceller."""


def _asyncio_scheduler(delay_ms: float, callback: Callable[[], None]) -> CancelTimer:
    """Schedule a callback on the running asyncio event loop.

    Args:
        delay_ms: Delay in milliseconds.
        callback: Zero-argument function to invoke when the delay elapses.

    Returns:
        A function that cancels the timer when called before it fires.
    """
    handle = asyncio.get_running_loop().call_later(delay_ms / 1000, callback)
    return handle.cancel


@ft.observable
class Toasts(ft.Observable):
    """Observable collection of active toasts with lifecycle orchestration.

    Mount a :class:`~flet_toastify.components.Toaster` bound to an instance
    (or to the default :data:`toast`) and call :meth:`show` or the
    type shortcuts from any event handler — re-rendering is automatic.

    Args:
        style: Default style, used for lifecycle timing and card rendering;
            defaults to ``ToastStyle()``. Per-toast styles take precedence.
        scheduler: Timer factory used for phase transitions and auto-dismiss.
            Defaults to asyncio-based timers; inject a fake in tests for
            deterministic control of time.
    """

    def __init__(
        self,
        style: ToastStyle | None = None,
        *,
        scheduler: Scheduler | None = None,
    ) -> None:
        self.toasts: list[Toast] = []
        self.style = style or ToastStyle()
        self._scheduler: Scheduler = scheduler or _asyncio_scheduler
        self._cancellers: dict[str, list[CancelTimer]] = {}

    def show(
        self,
        content: str | ft.Control,
        *,
        type: ToastType = ToastType.INFO,
        duration: int = DEFAULT_DURATION_MS,
        style: ToastStyle | None = None,
        index: int | None = None,
    ) -> str:
        """Display a new toast and schedule its lifecycle.

        Args:
            content: Plain message text or a custom Flet control.
            type: Semantic category driving default icon and colors.
            duration: Auto-dismiss timeout in milliseconds; ``0`` keeps the
                toast on screen until dismissed manually.
            style: Per-toast style override; ``None`` uses this instance's style.
            index: Position in the stack; ``None`` appends at the end.

        Returns:
            The id of the created toast, usable with :meth:`dismiss`.
        """
        new_toast = Toast(content, type=type, duration_ms=duration, style=style)
        if index is None:
            self.toasts.append(new_toast)
        else:
            self.toasts.insert(index, new_toast)
        self._schedule_lifecycle(new_toast)
        return new_toast.id

    def info(
        self,
        content: str | ft.Control,
        *,
        duration: int = DEFAULT_DURATION_MS,
        style: ToastStyle | None = None,
        index: int | None = None,
    ) -> str:
        """Display an info toast. See :meth:`show` for parameters."""
        return self.show(content, type=ToastType.INFO, duration=duration, style=style, index=index)

    def success(
        self,
        content: str | ft.Control,
        *,
        duration: int = DEFAULT_DURATION_MS,
        style: ToastStyle | None = None,
        index: int | None = None,
    ) -> str:
        """Display a success toast. See :meth:`show` for parameters."""
        return self.show(
            content, type=ToastType.SUCCESS, duration=duration, style=style, index=index
        )

    def warning(
        self,
        content: str | ft.Control,
        *,
        duration: int = DEFAULT_DURATION_MS,
        style: ToastStyle | None = None,
        index: int | None = None,
    ) -> str:
        """Display a warning toast. See :meth:`show` for parameters."""
        return self.show(
            content, type=ToastType.WARNING, duration=duration, style=style, index=index
        )

    def error(
        self,
        content: str | ft.Control,
        *,
        duration: int = DEFAULT_DURATION_MS,
        style: ToastStyle | None = None,
        index: int | None = None,
    ) -> str:
        """Display an error toast. See :meth:`show` for parameters."""
        return self.show(content, type=ToastType.ERROR, duration=duration, style=style, index=index)

    def dismiss(self, toast_id: str) -> None:
        """Start the exit animation of a toast and remove it when done.

        Cancels any pending timers (entrance transition, auto-dismiss) for
        the toast. Unknown ids and already-leaving toasts are ignored.

        Args:
            toast_id: Id returned by :meth:`show`.
        """
        found = self._find(toast_id)
        if found is None or found[1].phase is ToastPhase.LEAVING:
            return
        index, existing = found
        self._cancel_timers(toast_id)
        self.toasts[index] = existing.with_phase(ToastPhase.LEAVING)
        out_duration = self._style_for(existing).out_duration
        self._add_timer(toast_id, out_duration, lambda: self._remove(toast_id))

    def clear(self) -> None:
        """Remove all toasts immediately, cancelling every pending timer."""
        for toast_id in list(self._cancellers):
            self._cancel_timers(toast_id)
        self.toasts.clear()

    def _schedule_lifecycle(self, new_toast: Toast) -> None:
        """Schedule the entrance transition and optional auto-dismiss."""
        style = self._style_for(new_toast)
        toast_id = new_toast.id
        self._add_timer(
            toast_id,
            style.in_duration,
            lambda: self._set_phase(toast_id, ToastPhase.VISIBLE),
        )
        if new_toast.duration_ms > 0:
            self._add_timer(
                toast_id,
                style.in_duration + new_toast.duration_ms,
                lambda: self.dismiss(toast_id),
            )

    def _style_for(self, target: Toast) -> ToastStyle:
        """Return the effective style of a toast (per-toast override or default)."""
        return target.style or self.style

    def _add_timer(self, toast_id: str, delay_ms: float, callback: Callable[[], None]) -> None:
        """Schedule a callback and register its canceller under the toast id."""
        self._cancellers.setdefault(toast_id, []).append(self._scheduler(delay_ms, callback))

    def _cancel_timers(self, toast_id: str) -> None:
        """Cancel and forget every pending timer of a toast."""
        for cancel in self._cancellers.pop(toast_id, []):
            cancel()

    def _find(self, toast_id: str) -> tuple[int, Toast] | None:
        """Return ``(index, toast)`` for an id, or ``None`` when absent."""
        for index, existing in enumerate(self.toasts):
            if existing.id == toast_id:
                return index, existing
        return None

    def _set_phase(self, toast_id: str, phase: ToastPhase) -> None:
        """Replace a toast with a copy in the given phase, if still present."""
        found = self._find(toast_id)
        if found is not None:
            index, existing = found
            self.toasts[index] = existing.with_phase(phase)

    def _remove(self, toast_id: str) -> None:
        """Remove a toast from the list and drop its timer registry."""
        self._cancel_timers(toast_id)
        found = self._find(toast_id)
        if found is not None:
            del self.toasts[found[0]]


toast = Toasts()
"""Default :class:`Toasts` instance behind the global toast API.

A bare ``Toaster()`` binds to this instance, so ``toast.success("saved!")``
works from anywhere — the pattern popularized by react-toastify and sonner.
"""
