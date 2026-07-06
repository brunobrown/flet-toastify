"""Unit tests for ``ToastStyle`` in ``flet_toastify.style``."""

import flet as ft

from flet_toastify.style import ToastStyle
from flet_toastify.types import ToastType


class TestToastStyleDimensionDefaults:
    def test_dimensions(self):
        style = ToastStyle()

        assert style.height == 70
        assert style.width == 200
        assert style.spacing == 10
        assert style.border_radius == 5
        assert style.padding == 10


class TestToastStyleAnimationDefaults:
    def test_in_animation(self):
        style = ToastStyle()

        assert style.in_duration == 666
        assert style.in_offset == ft.Offset(0, 0)
        assert style.in_opacity == 0.0
        assert style.in_scale == 0.2

    def test_out_animation(self):
        style = ToastStyle()

        assert style.out_duration == 500
        assert style.out_offset == ft.Offset(0, 0)
        assert style.out_opacity == 0.0
        assert style.out_scale == 1.2

    def test_animation_curves_default_to_fast_out_slowin(self):
        style = ToastStyle()

        assert style.position_curve is ft.AnimationCurve.FAST_OUT_SLOWIN
        assert style.in_offset_curve is ft.AnimationCurve.FAST_OUT_SLOWIN
        assert style.out_offset_curve is ft.AnimationCurve.FAST_OUT_SLOWIN
        assert style.in_opacity_curve is ft.AnimationCurve.FAST_OUT_SLOWIN
        assert style.out_opacity_curve is ft.AnimationCurve.FAST_OUT_SLOWIN
        assert style.in_scale_curve is ft.AnimationCurve.FAST_OUT_SLOWIN
        assert style.out_scale_curve is ft.AnimationCurve.FAST_OUT_SLOWIN


class TestToastStyleTypeMapDefaults:
    def test_maps_are_keyed_by_toast_type(self):
        style = ToastStyle()

        for mapping in (style.bgcolors, style.icons, style.icon_colors, style.text_colors):
            assert set(mapping) == set(ToastType)

    def test_default_bgcolors(self):
        style = ToastStyle()

        assert style.bgcolors[ToastType.INFO] == ft.Colors.BLUE_100
        assert style.bgcolors[ToastType.SUCCESS] == ft.Colors.GREEN_ACCENT_100
        assert style.bgcolors[ToastType.WARNING] == ft.Colors.AMBER_100
        assert style.bgcolors[ToastType.ERROR] == ft.Colors.RED_ACCENT_100

    def test_default_icons(self):
        style = ToastStyle()

        assert style.icons[ToastType.INFO] == ft.Icons.INFO_OUTLINE
        assert style.icons[ToastType.SUCCESS] == ft.Icons.CHECK_CIRCLE_OUTLINE
        assert style.icons[ToastType.WARNING] == ft.Icons.WARNING_AMBER_ROUNDED
        assert style.icons[ToastType.ERROR] == ft.Icons.ERROR_OUTLINE

    def test_default_icon_and_text_colors(self):
        style = ToastStyle()

        expected = {
            ToastType.INFO: ft.Colors.BLUE_900,
            ToastType.SUCCESS: ft.Colors.GREEN_900,
            ToastType.WARNING: ft.Colors.AMBER_900,
            ToastType.ERROR: ft.Colors.RED_900,
        }
        assert style.icon_colors == expected
        assert style.text_colors == expected


class TestToastStyleResolution:
    def test_resolves_values_from_maps(self):
        style = ToastStyle()

        assert style.bgcolor_for(ToastType.SUCCESS) == ft.Colors.GREEN_ACCENT_100
        assert style.icon_for(ToastType.ERROR) == ft.Icons.ERROR_OUTLINE
        assert style.icon_color_for(ToastType.WARNING) == ft.Colors.AMBER_900
        assert style.text_color_for(ToastType.INFO) == ft.Colors.BLUE_900


class TestToastStylePartialOverride:
    def test_overridden_type_uses_custom_value(self):
        style = ToastStyle(bgcolors={ToastType.ERROR: ft.Colors.PURPLE_200})

        assert style.bgcolor_for(ToastType.ERROR) == ft.Colors.PURPLE_200

    def test_types_missing_from_override_fall_back(self):
        style = ToastStyle(bgcolors={ToastType.ERROR: ft.Colors.PURPLE_200})

        assert style.bgcolor_for(ToastType.INFO) == ft.Colors.PRIMARY_CONTAINER

    def test_dimension_override_keeps_other_defaults(self):
        style = ToastStyle(width=320)

        assert style.width == 320
        assert style.height == 70


class TestToastStyleFallbacks:
    def test_bgcolor_fallback(self):
        style = ToastStyle(bgcolors={})

        assert style.bgcolor_for(ToastType.INFO) == ft.Colors.PRIMARY_CONTAINER

    def test_icon_fallback(self):
        style = ToastStyle(icons={})

        assert style.icon_for(ToastType.INFO) == ft.Icons.NOTIFICATIONS_NONE

    def test_icon_color_fallback(self):
        style = ToastStyle(icon_colors={})

        assert style.icon_color_for(ToastType.INFO) == ft.Colors.PRIMARY

    def test_text_color_fallback(self):
        style = ToastStyle(text_colors={})

        assert style.text_color_for(ToastType.INFO) == ft.Colors.PRIMARY
