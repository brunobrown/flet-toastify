"""Visual and animation styling for toasts.

:class:`ToastStyle` groups every knob a user can turn: card dimensions,
entrance/exit animation parameters, and per-:class:`~flet_toastify.types.ToastType`
maps for background colors, icons, icon colors, and text colors. Resolution
methods (``*_for``) look values up by type and fall back to neutral theme
colors when a type is missing from an overridden map.
"""

from dataclasses import dataclass, field

import flet as ft

from flet_toastify.types import ToastType

__all__ = ["ToastStyle"]


def _default_bgcolors() -> dict[ToastType, ft.ColorValue]:
    """Return the default background color per toast type."""
    return {
        ToastType.INFO: ft.Colors.BLUE_100,
        ToastType.SUCCESS: ft.Colors.GREEN_ACCENT_100,
        ToastType.WARNING: ft.Colors.AMBER_100,
        ToastType.ERROR: ft.Colors.RED_ACCENT_100,
    }


def _default_icons() -> dict[ToastType, ft.IconData]:
    """Return the default icon per toast type."""
    return {
        ToastType.INFO: ft.Icons.INFO_OUTLINE,
        ToastType.SUCCESS: ft.Icons.CHECK_CIRCLE_OUTLINE,
        ToastType.WARNING: ft.Icons.WARNING_AMBER_ROUNDED,
        ToastType.ERROR: ft.Icons.ERROR_OUTLINE,
    }


def _default_accent_colors() -> dict[ToastType, ft.ColorValue]:
    """Return the default icon/text accent color per toast type."""
    return {
        ToastType.INFO: ft.Colors.BLUE_900,
        ToastType.SUCCESS: ft.Colors.GREEN_900,
        ToastType.WARNING: ft.Colors.AMBER_900,
        ToastType.ERROR: ft.Colors.RED_900,
    }


@dataclass(frozen=True)
class ToastStyle:
    """Styling and animation configuration for toast cards.

    All fields have sensible defaults; construct with keyword overrides to
    customize (e.g. ``ToastStyle(width=320, bgcolors={ToastType.ERROR: "red"})``).
    Per-type maps may be overridden partially — missing types resolve to
    neutral fallbacks via the ``*_for`` methods.
    """

    height: int = 70
    """Height of a toast card, in logical pixels."""

    width: int = 200
    """Width of a toast card, in logical pixels."""

    spacing: int = 10
    """Vertical gap between stacked toast cards, in logical pixels."""

    border_radius: int = 5
    """Corner radius of a toast card, in logical pixels."""

    padding: int = 10
    """Inner padding of a toast card, in logical pixels."""

    position_curve: ft.AnimationCurve = ft.AnimationCurve.FAST_OUT_SLOWIN
    """Curve applied when cards slide to a new stack position."""

    in_duration: int = 666
    """Entrance animation duration, in milliseconds."""

    in_offset: ft.Offset = field(default_factory=lambda: ft.Offset(0, 0))
    """Starting offset of the entrance animation."""

    in_offset_curve: ft.AnimationCurve = ft.AnimationCurve.FAST_OUT_SLOWIN
    """Curve of the entrance offset animation."""

    in_opacity: float = 0.0
    """Starting opacity of the entrance animation."""

    in_opacity_curve: ft.AnimationCurve = ft.AnimationCurve.FAST_OUT_SLOWIN
    """Curve of the entrance opacity animation."""

    in_scale: float = 0.2
    """Starting scale of the entrance animation."""

    in_scale_curve: ft.AnimationCurve = ft.AnimationCurve.FAST_OUT_SLOWIN
    """Curve of the entrance scale animation."""

    out_duration: int = 500
    """Exit animation duration, in milliseconds."""

    out_offset: ft.Offset = field(default_factory=lambda: ft.Offset(0, 0))
    """Ending offset of the exit animation."""

    out_offset_curve: ft.AnimationCurve = ft.AnimationCurve.FAST_OUT_SLOWIN
    """Curve of the exit offset animation."""

    out_opacity: float = 0.0
    """Ending opacity of the exit animation."""

    out_opacity_curve: ft.AnimationCurve = ft.AnimationCurve.FAST_OUT_SLOWIN
    """Curve of the exit opacity animation."""

    out_scale: float = 1.2
    """Ending scale of the exit animation."""

    out_scale_curve: ft.AnimationCurve = ft.AnimationCurve.FAST_OUT_SLOWIN
    """Curve of the exit scale animation."""

    show_progress: bool = True
    """Whether auto-dismiss toasts display a shrinking time-left bar."""

    progress_height: int = 4
    """Height of the auto-dismiss progress bar, in logical pixels."""

    bgcolors: dict[ToastType, ft.ColorValue] = field(default_factory=_default_bgcolors)
    """Background color per toast type."""

    icons: dict[ToastType, ft.IconData] = field(default_factory=_default_icons)
    """Icon per toast type."""

    icon_colors: dict[ToastType, ft.ColorValue] = field(default_factory=_default_accent_colors)
    """Icon color per toast type."""

    text_colors: dict[ToastType, ft.ColorValue] = field(default_factory=_default_accent_colors)
    """Text color per toast type."""

    progress_colors: dict[ToastType, ft.ColorValue] = field(default_factory=_default_accent_colors)
    """Progress bar color per toast type."""

    def bgcolor_for(self, type: ToastType) -> ft.ColorValue:
        """Return the background color for a toast type.

        Args:
            type: Toast type to resolve.

        Returns:
            The mapped color, or ``ft.Colors.PRIMARY_CONTAINER`` when the
            type is missing from :attr:`bgcolors`.
        """
        return self.bgcolors.get(type, ft.Colors.PRIMARY_CONTAINER)

    def icon_for(self, type: ToastType) -> ft.IconData:
        """Return the icon for a toast type.

        Args:
            type: Toast type to resolve.

        Returns:
            The mapped icon, or ``ft.Icons.NOTIFICATIONS_NONE`` when the
            type is missing from :attr:`icons`.
        """
        return self.icons.get(type, ft.Icons.NOTIFICATIONS_NONE)

    def icon_color_for(self, type: ToastType) -> ft.ColorValue:
        """Return the icon color for a toast type.

        Args:
            type: Toast type to resolve.

        Returns:
            The mapped color, or ``ft.Colors.PRIMARY`` when the type is
            missing from :attr:`icon_colors`.
        """
        return self.icon_colors.get(type, ft.Colors.PRIMARY)

    def text_color_for(self, type: ToastType) -> ft.ColorValue:
        """Return the text color for a toast type.

        Args:
            type: Toast type to resolve.

        Returns:
            The mapped color, or ``ft.Colors.PRIMARY`` when the type is
            missing from :attr:`text_colors`.
        """
        return self.text_colors.get(type, ft.Colors.PRIMARY)

    def progress_color_for(self, type: ToastType) -> ft.ColorValue:
        """Return the progress bar color for a toast type.

        Args:
            type: Toast type to resolve.

        Returns:
            The mapped color, or ``ft.Colors.PRIMARY`` when the type is
            missing from :attr:`progress_colors`.
        """
        return self.progress_colors.get(type, ft.Colors.PRIMARY)
