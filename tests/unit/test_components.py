"""Unit tests for the pure UI-building functions in ``flet_toastify.components``."""

from collections.abc import Callable
from typing import cast

import flet as ft
import pytest

from flet_toastify.components import (
    CardVisual,
    ToastCard,
    Toaster,
    build_card,
    card_offset_px,
    card_visual,
    position_wrapper,
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
        assert card.padding == STYLE.padding
        assert card.bgcolor == STYLE.bgcolor_for(ToastType.SUCCESS)

    def test_string_content_becomes_text_with_type_color(self):
        toast = Toast("hello", type=ToastType.ERROR)

        row = content_row(self._card(toast))

        icon, body, close = row.controls
        assert isinstance(icon, ft.Icon)
        assert icon.icon == STYLE.icon_for(ToastType.ERROR)
        assert icon.color == STYLE.icon_color_for(ToastType.ERROR)
        assert isinstance(body, ft.Text)
        assert body.value == "hello"
        assert body.color == STYLE.text_color_for(ToastType.ERROR)
        assert body.expand is True

    def test_control_content_is_used_as_is(self):
        custom = ft.Text("custom")
        toast = Toast(custom)

        row = content_row(self._card(toast))

        assert row.controls[1] is custom

    def test_close_button_triggers_on_dismiss(self):
        dismissed = []
        toast = Toast("hello")

        row = content_row(self._card(toast, on_dismiss=lambda: dismissed.append(True)))

        close = row.controls[2]
        assert isinstance(close, ft.IconButton)
        handler = cast("Callable[[object], None]", close.on_click)
        handler(None)
        assert dismissed == [True]

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
