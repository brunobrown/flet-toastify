"""Immutable data model of a single toast notification.

A :class:`Toast` is a value object: state transitions never mutate an
instance, they produce a new one (see :meth:`Toast.with_phase`). This keeps
the observable state layer trivially diffable by Flet's declarative
renderer.
"""

import uuid
from dataclasses import dataclass, field, replace

import flet as ft

from flet_toastify.style import ToastStyle
from flet_toastify.types import ToastPhase, ToastType

__all__ = ["DEFAULT_DURATION_MS", "Toast"]

DEFAULT_DURATION_MS = 5000
"""Default auto-dismiss timeout, matching react-toastify's ``autoClose``."""


def _new_toast_id() -> str:
    """Return a unique identifier for a new toast."""
    return uuid.uuid4().hex


@dataclass(frozen=True, slots=True)
class Toast:
    """A single toast notification, as stored in the observable state.

    Args:
        content: Plain message text or a custom Flet control to render.
        type: Semantic category driving default icon and colors.
        duration_ms: Auto-dismiss timeout in milliseconds; ``0`` keeps the
            toast on screen until dismissed manually.
        phase: Current animation lifecycle stage.
        id: Unique identifier; generated automatically when omitted.
        style: Per-toast style override; ``None`` uses the toaster's style.

    Raises:
        ValueError: If ``duration_ms`` is negative.
    """

    content: str | ft.Control
    """Plain message text or a custom Flet control to render."""

    type: ToastType = ToastType.INFO
    """Semantic category driving default icon and colors."""

    duration_ms: int = DEFAULT_DURATION_MS
    """Auto-dismiss timeout in milliseconds; ``0`` means persistent."""

    phase: ToastPhase = ToastPhase.ENTERING
    """Current animation lifecycle stage."""

    id: str = field(default_factory=_new_toast_id)
    """Unique identifier; generated automatically when omitted."""

    style: ToastStyle | None = None
    """Per-toast style override; ``None`` uses the toaster's style."""

    def __post_init__(self) -> None:
        """Validate field invariants after initialization."""
        if self.duration_ms < 0:
            raise ValueError(
                f"duration_ms must be >= 0 (0 means persistent), got {self.duration_ms}"
            )

    def with_phase(self, phase: ToastPhase) -> Toast:
        """Return a copy of this toast in the given lifecycle phase.

        Args:
            phase: Target lifecycle stage.

        Returns:
            A new :class:`Toast` identical to this one except for ``phase``.
        """
        return replace(self, phase=phase)
