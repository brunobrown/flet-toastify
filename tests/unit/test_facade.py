"""Unit tests for the public package facade (``flet_toastify.__init__``)."""

import flet_toastify
from flet_toastify import (
    Position,
    Toast,
    Toaster,
    ToastPhase,
    Toasts,
    ToastStyle,
    ToastType,
    toast,
)

EXPECTED_EXPORTS = {
    "Position",
    "Toast",
    "ToastCard",
    "ToastPhase",
    "ToastStyle",
    "ToastType",
    "Toaster",
    "Toasts",
    "toast",
}


class TestPublicApi:
    def test_all_matches_expected_exports(self):
        assert set(flet_toastify.__all__) == EXPECTED_EXPORTS

    def test_all_names_resolve_to_module_attributes(self):
        for name in flet_toastify.__all__:
            assert getattr(flet_toastify, name) is not None

    def test_facade_reexports_the_real_objects(self):
        from flet_toastify import components, models, state, style, types

        assert Toast is models.Toast
        assert ToastStyle is style.ToastStyle
        assert Toasts is state.Toasts
        assert toast is state.toast
        assert Toaster is components.Toaster
        assert ToastType is types.ToastType
        assert ToastPhase is types.ToastPhase
        assert Position is types.Position

    def test_default_toast_is_a_toasts_instance(self):
        assert isinstance(toast, Toasts)
