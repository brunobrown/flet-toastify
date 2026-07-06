"""Unit tests for the pure UI-building functions in ``flet_toastify.components``."""

from collections.abc import Callable
from types import SimpleNamespace
from typing import cast

import flet as ft
import pytest

from flet_toastify.components import (
    SETTLE_DELAY_MS,
    CardVisual,
    ProgressVisual,
    ToastCard,
    Toaster,
    build_card,
    build_progress_bar,
    card_offset_px,
    card_visual,
    position_wrapper,
    progress_visual,
    row_alignment,
    stack_coordinates,
)
from flet_toastify.models import Toast
from flet_toastify.style import ToastStyle
from flet_toastify.types import Position, ToastPhase, ToastType

STYLE = ToastStyle()


def content_row(container: ft.Container) -> ft.Row:
    """Return the container's content, narrowed to the expected ft.Row."""
    assert isinstance(container.content, ft.Row)
    return container.content


def card_layers(card: ft.Container) -> list[ft.Control]:
    """Return the layers of a card's inner stack (content layer + optional bar)."""
    assert isinstance(card.content, ft.Stack)
    return card.content.controls


def card_body(card: ft.Container) -> ft.Container:
    """Return the padded content layer of a card, narrowed to ft.Container."""
    body = card_layers(card)[0]
    assert isinstance(body, ft.Container)
    return body


def card_row(card: ft.Container) -> ft.Row:
    """Return the icon/content/close row of a card."""
    return content_row(card_body(card))


def card_progress(card: ft.Container) -> ft.Container | None:
    """Return the card's progress bar layer, or ``None`` when absent."""
    layers = card_layers(card)
    if len(layers) < 2:
        return None
    bar = layers[1]
    assert isinstance(bar, ft.Container)
    return bar


class TestCardOffsetPx:
    def test_first_card_sits_one_spacing_from_the_edge(self):
        assert card_offset_px(0, STYLE) == STYLE.spacing

    def test_offset_grows_by_height_plus_spacing_per_index(self):
        expected = STYLE.spacing + 2 * (STYLE.height + STYLE.spacing)

        assert card_offset_px(2, STYLE) == expected


class TestStackCoordinates:
    @pytest.mark.parametrize(
        "position",
        [Position.TOP_LEFT, Position.TOP_CENTER, Position.TOP_RIGHT],
    )
    def test_top_positions_anchor_to_top(self, position):
        assert stack_coordinates(position, 25) == (25, None)

    @pytest.mark.parametrize(
        "position",
        [Position.BOTTOM_LEFT, Position.BOTTOM_CENTER, Position.BOTTOM_RIGHT],
    )
    def test_bottom_positions_anchor_to_bottom(self, position):
        assert stack_coordinates(position, 25) == (None, 25)


class TestRowAlignment:
    @pytest.mark.parametrize(
        ("position", "alignment"),
        [
            (Position.TOP_LEFT, ft.MainAxisAlignment.START),
            (Position.BOTTOM_LEFT, ft.MainAxisAlignment.START),
            (Position.TOP_CENTER, ft.MainAxisAlignment.CENTER),
            (Position.BOTTOM_CENTER, ft.MainAxisAlignment.CENTER),
            (Position.TOP_RIGHT, ft.MainAxisAlignment.END),
            (Position.BOTTOM_RIGHT, ft.MainAxisAlignment.END),
        ],
    )
    def test_horizontal_alignment_per_position(self, position, alignment):
        assert row_alignment(position) is alignment


class TestCardVisual:
    def test_entering_not_settled_uses_in_start_values(self):
        visual = card_visual(ToastPhase.ENTERING, False, STYLE)

        assert visual == CardVisual(
            opacity=STYLE.in_opacity,
            scale=STYLE.in_scale,
            offset=STYLE.in_offset,
            animate_opacity=ft.Animation(STYLE.in_duration, STYLE.in_opacity_curve),
            animate_scale=ft.Animation(STYLE.in_duration, STYLE.in_scale_curve),
            animate_offset=ft.Animation(STYLE.in_duration, STYLE.in_offset_curve),
        )

    def test_entering_settled_rests_at_full_visibility(self):
        visual = card_visual(ToastPhase.ENTERING, True, STYLE)

        assert visual.opacity == 1.0
        assert visual.scale == 1.0
        assert visual.offset == ft.Offset(0, 0)
        assert visual.animate_opacity == ft.Animation(STYLE.in_duration, STYLE.in_opacity_curve)

    def test_visible_rests_at_full_visibility(self):
        visual = card_visual(ToastPhase.VISIBLE, True, STYLE)

        assert visual.opacity == 1.0
        assert visual.scale == 1.0
        assert visual.offset == ft.Offset(0, 0)

    def test_leaving_uses_out_end_values_and_out_animations(self):
        visual = card_visual(ToastPhase.LEAVING, True, STYLE)

        assert visual == CardVisual(
            opacity=STYLE.out_opacity,
            scale=STYLE.out_scale,
            offset=STYLE.out_offset,
            animate_opacity=ft.Animation(STYLE.out_duration, STYLE.out_opacity_curve),
            animate_scale=ft.Animation(STYLE.out_duration, STYLE.out_scale_curve),
            animate_offset=ft.Animation(STYLE.out_duration, STYLE.out_offset_curve),
        )


class TestBuildCard:
    def _card(self, toast: Toast, *, settled: bool = True, on_dismiss=lambda: None):
        return build_card(toast, STYLE, settled, on_dismiss)

    def test_card_dimensions_and_colors_come_from_style_and_type(self):
        toast = Toast("hello", type=ToastType.SUCCESS)

        card = self._card(toast)

        assert card.key == toast.id
        assert card.height == STYLE.height
        assert card.width == STYLE.width
        assert card.border_radius == STYLE.border_radius
        assert card.clip_behavior is ft.ClipBehavior.ANTI_ALIAS
        assert card.bgcolor == STYLE.bgcolor_for(ToastType.SUCCESS)
        assert card_body(card).padding == STYLE.padding

    def test_string_content_becomes_text_with_type_color(self):
        toast = Toast("hello", type=ToastType.ERROR)

        row = card_row(self._card(toast))

        icon, body, close = row.controls
        assert isinstance(icon, ft.Icon)
        assert icon.icon == STYLE.icon_for(ToastType.ERROR)
        assert icon.color == STYLE.icon_color_for(ToastType.ERROR)
        assert isinstance(body, ft.Text)
        assert body.value == "hello"
        assert body.color == STYLE.text_color_for(ToastType.ERROR)
        assert body.expand is True
        assert body.selectable is True

    def test_control_content_is_used_as_is(self):
        custom = ft.Text("custom")
        toast = Toast(custom)

        row = card_row(self._card(toast))

        assert row.controls[1] is custom

    def test_close_button_triggers_on_dismiss(self):
        dismissed = []
        toast = Toast("hello")

        row = card_row(self._card(toast, on_dismiss=lambda: dismissed.append(True)))

        close = row.controls[2]
        assert isinstance(close, ft.IconButton)
        handler = cast("Callable[[object], None]", close.on_click)
        handler(None)
        assert dismissed == [True]

    def test_hover_enter_pauses_and_exit_resumes(self):
        calls = []
        toast = Toast("hello")

        card = build_card(
            toast,
            STYLE,
            True,
            lambda: None,
            on_pause=lambda: calls.append("pause"),
            on_resume=lambda: calls.append("resume"),
        )

        hover = cast("Callable[[object], None]", card.on_hover)
        hover(SimpleNamespace(data=True))
        hover(SimpleNamespace(data=False))
        assert calls == ["pause", "resume"]

    def test_card_applies_visual_state_for_phase(self):
        toast = Toast("hello")

        card = self._card(toast, settled=False)

        visual = card_visual(ToastPhase.ENTERING, False, STYLE)
        assert card.opacity == visual.opacity
        assert card.scale == visual.scale
        assert card.offset == visual.offset
        assert card.animate_opacity == visual.animate_opacity
        assert card.animate_scale == visual.animate_scale
        assert card.animate_offset == visual.animate_offset


class TestProgressVisual:
    def test_persistent_toast_has_no_progress(self):
        toast = Toast("pinned", duration_ms=0)

        assert progress_visual(toast, STYLE, settled=False) is None

    def test_disabled_progress_has_no_progress(self):
        toast = Toast("hello")
        style = ToastStyle(show_progress=False)

        assert progress_visual(toast, style, settled=False) is None

    def test_not_settled_starts_at_full_width(self):
        toast = Toast("hello", duration_ms=3000)

        visual = progress_visual(toast, STYLE, settled=False)

        assert visual is not None
        assert visual.width == STYLE.width

    def test_settled_shrinks_to_zero_over_remaining_lifetime(self):
        toast = Toast("hello", duration_ms=3000)

        visual = progress_visual(toast, STYLE, settled=True)

        expected_ms = STYLE.in_duration + 3000 - SETTLE_DELAY_MS
        assert visual == ProgressVisual(
            width=0,
            height=STYLE.progress_height,
            color=STYLE.progress_color_for(ToastType.INFO),
            animate=ft.Animation(expected_ms, ft.AnimationCurve.LINEAR),
        )

    def test_color_and_height_come_from_style_and_type(self):
        toast = Toast("boom", type=ToastType.ERROR, duration_ms=3000)

        visual = progress_visual(toast, STYLE, settled=False)

        assert visual is not None
        assert visual.color == STYLE.progress_color_for(ToastType.ERROR)
        assert visual.height == STYLE.progress_height

    def test_animation_duration_never_drops_below_one_ms(self):
        toast = Toast("fast", duration_ms=1)
        style = ToastStyle(in_duration=1)

        visual = progress_visual(toast, style, settled=True)

        assert visual is not None
        assert visual.animate.duration == 1

    def test_paused_toast_freezes_bar_at_remaining_fraction(self):
        total = STYLE.in_duration + 3000 - SETTLE_DELAY_MS
        toast = Toast("hello", duration_ms=3000).with_pause(1500)

        visual = progress_visual(toast, STYLE, settled=True)

        assert visual is not None
        assert visual.width == STYLE.width * 1500 / total
        assert visual.animate == ft.Animation(1, ft.AnimationCurve.LINEAR)

    def test_paused_fraction_is_clamped_to_full_width(self):
        toast = Toast("hello", duration_ms=3000).with_pause(999_999)

        visual = progress_visual(toast, STYLE, settled=True)

        assert visual is not None
        assert visual.width == STYLE.width

    def test_resumed_toast_shrinks_over_remaining_time(self):
        toast = Toast("hello", duration_ms=3000).with_pause(1500).with_resume()

        visual = progress_visual(toast, STYLE, settled=True)

        assert visual is not None
        assert visual.width == 0
        assert visual.animate == ft.Animation(1500, ft.AnimationCurve.LINEAR)


class TestBuildProgressBar:
    def test_returns_none_for_persistent_toast(self):
        toast = Toast("pinned", duration_ms=0)

        assert build_progress_bar(toast, STYLE, settled=False) is None

    def test_bar_is_anchored_to_bottom_left(self):
        toast = Toast("hello", duration_ms=3000)

        bar = build_progress_bar(toast, STYLE, settled=False)

        assert bar is not None
        assert bar.bottom == 0
        assert bar.left == 0
        assert bar.height == STYLE.progress_height
        assert bar.width == STYLE.width
        assert bar.bgcolor == STYLE.progress_color_for(ToastType.INFO)
        assert bar.animate == ft.Animation(STYLE.in_duration + 3000 - 50, ft.AnimationCurve.LINEAR)


class TestBuildCardProgress:
    def test_auto_dismiss_card_includes_progress_bar(self):
        toast = Toast("hello", type=ToastType.ERROR, duration_ms=3000)

        card = build_card(toast, STYLE, False, lambda: None)

        bar = card_progress(card)
        assert bar is not None
        assert bar.bgcolor == STYLE.progress_color_for(ToastType.ERROR)

    def test_persistent_card_has_no_progress_bar(self):
        toast = Toast("pinned", duration_ms=0)

        card = build_card(toast, STYLE, False, lambda: None)

        assert card_progress(card) is None

    def test_settled_card_bar_targets_zero_width(self):
        toast = Toast("hello", duration_ms=3000)

        card = build_card(toast, STYLE, True, lambda: None)

        bar = card_progress(card)
        assert bar is not None
        assert bar.width == 0


class TestPositionWrapper:
    def test_wrapper_anchors_and_aligns_child(self):
        child = ft.Text("card")

        wrapper = position_wrapper(
            child, index=1, position=Position.BOTTOM_LEFT, style=STYLE, key="w1"
        )

        assert wrapper.key == "w1"
        assert wrapper.top is None
        assert wrapper.bottom == card_offset_px(1, STYLE)
        assert wrapper.left == 0
        assert wrapper.right == 0
        assert wrapper.animate_position == ft.Animation(STYLE.in_duration, STYLE.position_curve)
        row = content_row(wrapper)
        assert row.alignment is ft.MainAxisAlignment.START
        assert row.controls == [child]

    def test_wrapper_top_anchor(self):
        child = ft.Text("card")

        wrapper = position_wrapper(
            child, index=0, position=Position.TOP_RIGHT, style=STYLE, key="w2"
        )

        assert wrapper.top == card_offset_px(0, STYLE)
        assert wrapper.bottom is None
        assert content_row(wrapper).alignment is ft.MainAxisAlignment.END


class TestComponents:
    def test_toast_card_and_toaster_are_flet_components(self):
        assert getattr(ToastCard, "__is_component__", False)
        assert getattr(Toaster, "__is_component__", False)
