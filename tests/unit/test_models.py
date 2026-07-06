"""Unit tests for the ``Toast`` model in ``flet_toastify.models``."""

import dataclasses

import flet as ft
import pytest

from flet_toastify.models import DEFAULT_DURATION_MS, Toast
from flet_toastify.style import ToastStyle
from flet_toastify.types import ToastPhase, ToastType


class TestToastDefaults:
    def test_creation_with_message_only(self):
        toast = Toast("File saved!")

        assert toast.content == "File saved!"
        assert toast.type is ToastType.INFO
        assert toast.duration_ms == DEFAULT_DURATION_MS
        assert toast.phase is ToastPhase.ENTERING

    def test_id_is_generated_automatically(self):
        toast = Toast("hello")

        assert isinstance(toast.id, str)
        assert toast.id

    def test_ids_are_unique(self):
        ids = {Toast("hello").id for _ in range(100)}

        assert len(ids) == 100

    def test_accepts_control_content(self):
        content = ft.Text("custom content")

        toast = Toast(content)

        assert toast.content is content

    def test_accepts_explicit_fields(self):
        toast = Toast(
            "boom",
            type=ToastType.ERROR,
            duration_ms=1500,
            phase=ToastPhase.VISIBLE,
            id="custom-id",
        )

        assert toast.type is ToastType.ERROR
        assert toast.duration_ms == 1500
        assert toast.phase is ToastPhase.VISIBLE
        assert toast.id == "custom-id"


class TestToastDurationValidation:
    def test_negative_duration_is_rejected(self):
        with pytest.raises(ValueError, match="duration_ms"):
            Toast("hello", duration_ms=-1)

    def test_zero_duration_means_persistent_and_is_allowed(self):
        toast = Toast("hello", duration_ms=0)

        assert toast.duration_ms == 0


class TestToastStyleField:
    def test_style_defaults_to_none(self):
        toast = Toast("hello")

        assert toast.style is None

    def test_accepts_custom_style(self):
        style = ToastStyle(width=320)

        toast = Toast("hello", style=style)

        assert toast.style is style

    def test_with_phase_preserves_style(self):
        style = ToastStyle()
        toast = Toast("hello", style=style)

        leaving = toast.with_phase(ToastPhase.LEAVING)

        assert leaving.style is style


class TestToastPhaseTransition:
    def test_with_phase_returns_new_toast_in_target_phase(self):
        toast = Toast("hello")

        visible = toast.with_phase(ToastPhase.VISIBLE)

        assert visible.phase is ToastPhase.VISIBLE
        assert visible is not toast

    def test_with_phase_preserves_identity_and_payload(self):
        toast = Toast("hello", type=ToastType.SUCCESS, duration_ms=2000)

        leaving = toast.with_phase(ToastPhase.LEAVING)

        assert leaving.id == toast.id
        assert leaving.content == toast.content
        assert leaving.type is toast.type
        assert leaving.duration_ms == toast.duration_ms

    def test_original_toast_is_not_mutated(self):
        toast = Toast("hello")

        toast.with_phase(ToastPhase.LEAVING)

        assert toast.phase is ToastPhase.ENTERING


class TestToastImmutability:
    def test_toast_is_frozen(self):
        toast = Toast("hello")

        with pytest.raises(dataclasses.FrozenInstanceError):
            toast.phase = ToastPhase.VISIBLE  # ty: ignore[invalid-assignment]
