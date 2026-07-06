"""Domain enums shared across the flet-toastify package.

These string enums describe the toast vocabulary: semantic type
(:class:`ToastType`), animation lifecycle (:class:`ToastPhase`), and
on-screen placement of the toaster stack (:class:`Position`).
"""

from enum import StrEnum

__all__ = ["Position", "ToastPhase", "ToastType"]


class ToastType(StrEnum):
    """Semantic category of a toast, driving its default icon and colors."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class ToastPhase(StrEnum):
    """Animation lifecycle stage of a toast.

    A toast is created in ``ENTERING``, settles into ``VISIBLE`` once the
    entrance animation completes, and moves to ``LEAVING`` when dismissed —
    it is removed from state after the exit animation finishes.
    """

    ENTERING = "entering"
    VISIBLE = "visible"
    LEAVING = "leaving"


class Position(StrEnum):
    """Corner or edge of the page where a toaster stacks its toasts."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
