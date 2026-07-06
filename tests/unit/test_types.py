"""Unit tests for the domain enums in ``flet_toastify.types``."""

from enum import StrEnum

from flet_toastify.types import Position, ToastPhase, ToastType


class TestToastType:
    def test_members(self):
        assert [member.name for member in ToastType] == [
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
        ]

    def test_values_are_lowercase_strings(self):
        assert ToastType.INFO == "info"
        assert ToastType.SUCCESS == "success"
        assert ToastType.WARNING == "warning"
        assert ToastType.ERROR == "error"

    def test_is_str_enum(self):
        assert issubclass(ToastType, StrEnum)


class TestToastPhase:
    def test_members(self):
        assert [member.name for member in ToastPhase] == [
            "ENTERING",
            "VISIBLE",
            "LEAVING",
        ]

    def test_values_are_lowercase_strings(self):
        assert ToastPhase.ENTERING == "entering"
        assert ToastPhase.VISIBLE == "visible"
        assert ToastPhase.LEAVING == "leaving"

    def test_is_str_enum(self):
        assert issubclass(ToastPhase, StrEnum)


class TestPosition:
    def test_has_six_positions(self):
        assert len(Position) == 6

    def test_members(self):
        assert [member.name for member in Position] == [
            "TOP_LEFT",
            "TOP_CENTER",
            "TOP_RIGHT",
            "BOTTOM_LEFT",
            "BOTTOM_CENTER",
            "BOTTOM_RIGHT",
        ]

    def test_values_are_lowercase_strings(self):
        assert Position.TOP_LEFT == "top_left"
        assert Position.TOP_CENTER == "top_center"
        assert Position.TOP_RIGHT == "top_right"
        assert Position.BOTTOM_LEFT == "bottom_left"
        assert Position.BOTTOM_CENTER == "bottom_center"
        assert Position.BOTTOM_RIGHT == "bottom_right"

    def test_is_str_enum(self):
        assert issubclass(Position, StrEnum)
