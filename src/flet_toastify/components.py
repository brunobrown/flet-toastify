"""Declarative UI components: ``ToastCard`` and ``Toaster``.

The ``@ft.component`` functions are the thinnest possible glue: all layout
math and control construction lives in pure, unit-testable functions
(:func:`card_visual`, :func:`build_card`, :func:`position_wrapper`, ...).
Flet controls are plain dataclasses, so these builders run without a page
or renderer.

``Toaster`` is the equivalent of react-toastify's ``<ToastContainer />``:
mount it once inside a ``ft.Stack`` and it re-renders automatically whenever
its bound :class:`~flet_toastify.state.Toasts` instance changes.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from flet_toastify.models import Toast
from flet_toastify.state import Toasts
from flet_toastify.state import toast as _default_toasts
from flet_toastify.style import ToastStyle
from flet_toastify.types import Position, ToastPhase

__all__ = ["ToastCard", "Toaster"]

SETTLE_DELAY_MS = 50
"""Delay before flipping a card to its resting visuals, letting the client
paint the initial (start-of-animation) frame first."""

_SETTLE_DELAY_S = SETTLE_DELAY_MS / 1000

_ROW_ALIGNMENTS = {
    "left": ft.MainAxisAlignment.START,
    "center": ft.MainAxisAlignment.CENTER,
    "right": ft.MainAxisAlignment.END,
}


@dataclass(frozen=True)
class CardVisual:
    """Resolved animation-related visual properties of a toast card."""

    opacity: float
    """Card opacity for the current phase."""

    scale: float
    """Card scale for the current phase."""

    offset: ft.Offset
    """Card offset for the current phase."""

    animate_opacity: ft.Animation
    """Implicit animation applied to opacity changes."""

    animate_scale: ft.Animation
    """Implicit animation applied to scale changes."""

    animate_offset: ft.Animation
    """Implicit animation applied to offset changes."""


def card_offset_px(index: int, style: ToastStyle) -> int:
    """Return the distance of a card from its anchored edge, in pixels.

    Args:
        index: Zero-based position of the card in the stack.
        style: Style providing card height and spacing.

    Returns:
        ``spacing + index * (height + spacing)`` — one spacing from the
        edge, then one card slot per index.
    """
    return style.spacing + index * (style.height + style.spacing)


def stack_coordinates(position: Position, offset_px: int) -> tuple[int | None, int | None]:
    """Return the ``(top, bottom)`` stack coordinates for a card wrapper.

    Args:
        position: Toaster placement on the page.
        offset_px: Distance from the anchored edge (see :func:`card_offset_px`).

    Returns:
        ``(offset_px, None)`` for top positions, ``(None, offset_px)`` for
        bottom positions.
    """
    if position.startswith("top"):
        return offset_px, None
    return None, offset_px


def row_alignment(position: Position) -> ft.MainAxisAlignment:
    """Return the horizontal alignment of a card row for a toaster position.

    Args:
        position: Toaster placement on the page.

    Returns:
        ``START`` for left, ``CENTER`` for center, ``END`` for right.
    """
    return _ROW_ALIGNMENTS[position.rsplit("_", 1)[1]]


def card_visual(phase: ToastPhase, settled: bool, style: ToastStyle) -> CardVisual:
    """Resolve the visual properties of a card for its lifecycle moment.

    Args:
        phase: Current lifecycle phase of the toast.
        settled: Whether the card already flipped to its resting visuals
            (the entrance animation runs on the ``False`` → ``True`` change).
        style: Style providing animation values and curves.

    Returns:
        Start-of-entrance values while ``ENTERING`` and not settled,
        end-of-exit values while ``LEAVING``, resting values otherwise.
    """
    if phase is ToastPhase.LEAVING:
        return CardVisual(
            opacity=style.out_opacity,
            scale=style.out_scale,
            offset=style.out_offset,
            animate_opacity=ft.Animation(style.out_duration, style.out_opacity_curve),
            animate_scale=ft.Animation(style.out_duration, style.out_scale_curve),
            animate_offset=ft.Animation(style.out_duration, style.out_offset_curve),
        )
    at_start = phase is ToastPhase.ENTERING and not settled
    return CardVisual(
        opacity=style.in_opacity if at_start else 1.0,
        scale=style.in_scale if at_start else 1.0,
        offset=style.in_offset if at_start else ft.Offset(0, 0),
        animate_opacity=ft.Animation(style.in_duration, style.in_opacity_curve),
        animate_scale=ft.Animation(style.in_duration, style.in_scale_curve),
        animate_offset=ft.Animation(style.in_duration, style.in_offset_curve),
    )


@dataclass(frozen=True)
class ProgressVisual:
    """Resolved visual properties of the auto-dismiss progress bar."""

    width: float
    """Bar width: full card width at start, ``0`` once settled."""

    height: int
    """Bar height, from :attr:`ToastStyle.progress_height`."""

    color: ft.ColorValue
    """Bar color for the toast type."""

    animate: ft.Animation
    """Linear animation covering the toast's remaining lifetime."""


def progress_visual(toast: Toast, style: ToastStyle, settled: bool) -> ProgressVisual | None:
    """Resolve the time-left progress bar visuals for a toast.

    The bar renders at full width, then shrinks linearly to zero exactly
    when the auto-dismiss timer fires (entrance duration plus toast
    duration, minus the settle delay that triggers the shrink).

    While the toast is paused (see :meth:`~flet_toastify.state.Toasts.pause`)
    the bar freezes at the fraction of lifetime left; on resume it shrinks
    to zero over the recorded remaining time.

    Args:
        toast: Toast being rendered.
        style: Effective style of the card.
        settled: Whether the card already flipped to its resting visuals.

    Returns:
        The resolved bar visuals, or ``None`` for persistent toasts
        (``duration_ms == 0``) and styles with ``show_progress=False``.
    """
    if not style.show_progress or toast.duration_ms <= 0:
        return None
    total_ms = max(style.in_duration + toast.duration_ms - SETTLE_DELAY_MS, 1)
    if toast.paused:
        fraction = min((toast.remaining_ms or 0) / total_ms, 1.0)
        return ProgressVisual(
            width=style.width * fraction,
            height=style.progress_height,
            color=style.progress_color_for(toast.type),
            animate=ft.Animation(1, ft.AnimationCurve.LINEAR),
        )
    remaining_ms = total_ms if toast.remaining_ms is None else max(toast.remaining_ms, 1)
    return ProgressVisual(
        width=0 if settled else style.width,
        height=style.progress_height,
        color=style.progress_color_for(toast.type),
        animate=ft.Animation(remaining_ms, ft.AnimationCurve.LINEAR),
    )


def build_progress_bar(
    toast: Toast,
    style: ToastStyle,
    settled: bool,
) -> ft.Container | None:
    """Build the shrinking time-left bar anchored to the card's bottom.

    Args:
        toast: Toast being rendered.
        style: Effective style of the card.
        settled: Whether the card already flipped to its resting visuals.

    Returns:
        The bar control, or ``None`` when the toast shows no progress bar
        (see :func:`progress_visual`).
    """
    visual = progress_visual(toast, style, settled)
    if visual is None:
        return None
    return ft.Container(
        left=0,
        bottom=0,
        width=visual.width,
        height=visual.height,
        bgcolor=visual.color,
        animate=visual.animate,
    )


def _noop() -> None:
    """Do nothing; default for optional card callbacks."""


def build_card(
    toast: Toast,
    style: ToastStyle,
    settled: bool,
    on_dismiss: Callable[[], None],
    *,
    on_pause: Callable[[], None] = _noop,
    on_resume: Callable[[], None] = _noop,
) -> ft.Container:
    """Build the visual card control for a toast.

    Args:
        toast: Toast to render.
        style: Effective style of the card.
        settled: Whether the card already flipped to its resting visuals.
        on_dismiss: Invoked when the close button is clicked.
        on_pause: Invoked when the pointer enters the card (hover start).
        on_resume: Invoked when the pointer leaves the card (hover end).

    Returns:
        A ``ft.Container`` with icon, content, close button, an optional
        time-left progress bar, and animation properties resolved from the
        toast phase and style.
    """
    visual = card_visual(toast.phase, settled, style)
    body: ft.Control
    if isinstance(toast.content, ft.Control):
        body = toast.content
    else:
        body = ft.Text(
            toast.content,
            color=style.text_color_for(toast.type),
            expand=True,
            selectable=True,
        )
    content_layer = ft.Container(
        left=0,
        top=0,
        right=0,
        bottom=0,
        padding=style.padding,
        content=ft.Row(
            [
                ft.Icon(style.icon_for(toast.type), color=style.icon_color_for(toast.type)),
                body,
                ft.IconButton(
                    ft.Icons.CLOSE,
                    icon_color=style.icon_color_for(toast.type),
                    icon_size=14,
                    on_click=lambda _: on_dismiss(),
                ),
            ]
        ),
    )
    progress_bar = build_progress_bar(toast, style, settled)
    layers: list[ft.Control] = [content_layer]
    if progress_bar is not None:
        layers.append(progress_bar)
    return ft.Container(
        key=toast.id,
        height=style.height,
        width=style.width,
        bgcolor=style.bgcolor_for(toast.type),
        border_radius=style.border_radius,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        opacity=visual.opacity,
        scale=visual.scale,
        offset=visual.offset,
        animate_opacity=visual.animate_opacity,
        animate_scale=visual.animate_scale,
        animate_offset=visual.animate_offset,
        on_hover=lambda e: on_pause() if e.data else on_resume(),
        content=ft.Stack(layers),
    )


def position_wrapper(
    child: ft.Control,
    *,
    index: int,
    position: Position,
    style: ToastStyle,
    key: str,
) -> ft.Container:
    """Wrap a card so it lands on the right spot of the toaster stack.

    Args:
        child: Card control to place.
        index: Zero-based position of the card in the stack.
        position: Toaster placement on the page.
        style: Toaster-level style, used for stack geometry.
        key: Stable key so reordering animates instead of rebuilding.

    Returns:
        A full-width ``ft.Container`` anchored to the top or bottom edge,
        with the card horizontally aligned per ``position`` and smooth
        position changes via ``animate_position``.
    """
    top, bottom = stack_coordinates(position, card_offset_px(index, style))
    return ft.Container(
        key=key,
        top=top,
        bottom=bottom,
        left=0,
        right=0,
        animate_position=ft.Animation(style.in_duration, style.position_curve),
        content=ft.Row([child], alignment=row_alignment(position)),
    )


@ft.component
def ToastCard(
    toast: Toast,
    toasts: Toasts,
    style: ToastStyle,
    key: str | None = None,
) -> ft.Control:  # pragma: no cover
    """Render a single toast card bound to its ``Toasts`` state.

    A local ``settled`` flag flips shortly after mount so the client paints
    the start-of-entrance frame first and then animates to the resting
    visuals over ``style.in_duration``.

    Args:
        toast: Toast to render.
        toasts: State instance that owns the toast (targets of dismissal).
        style: Effective style of the card.
        key: Stable component key; consumed by the Flet renderer for
            reconciliation, never received by this function.
    """
    settled, set_settled = ft.use_state(False)

    async def settle():
        await asyncio.sleep(_SETTLE_DELAY_S)
        # ty pins StateT to Literal[False] from the initial value.
        set_settled(True)  # ty: ignore[invalid-argument-type]

    ft.use_effect(settle)
    return build_card(
        toast,
        style,
        settled,
        lambda: toasts.dismiss(toast.id),
        on_pause=lambda: toasts.pause(toast.id),
        on_resume=lambda: toasts.resume(toast.id),
    )


@ft.component
def Toaster(
    toasts: Toasts | None = None,
    position: Position = Position.TOP_RIGHT,
    style: ToastStyle | None = None,
) -> ft.Control:  # pragma: no cover
    """Render the stack of active toasts for a ``Toasts`` instance.

    Mount it once inside a ``ft.Stack`` — the equivalent of react-toastify's
    ``<ToastContainer />``. Re-renders automatically whenever the bound
    state changes.

    Args:
        toasts: State instance to render; ``None`` binds to the default
            global :data:`~flet_toastify.state.toast` instance.
        position: Corner or edge where toasts stack up.
        style: Toaster-level style override; ``None`` uses the state
            instance's style. Per-toast styles win for card rendering,
            while stack geometry always follows the toaster-level style.
    """
    state, _ = ft.use_state(toasts or _default_toasts)
    toaster_style = style or state.style
    return ft.Stack(
        expand=True,
        controls=[
            position_wrapper(
                ToastCard(item, state, item.style or toaster_style, key=item.id),
                index=index,
                position=position,
                style=toaster_style,
                key=f"slot-{item.id}",
            )
            for index, item in enumerate(state.toasts)
        ],
    )
