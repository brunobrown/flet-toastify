"""Unit tests for the observable ``Toasts`` state in ``flet_toastify.state``."""

import asyncio

import flet as ft

import flet_toastify
from flet_toastify.models import DEFAULT_DURATION_MS
from flet_toastify.state import Toasts, toast
from flet_toastify.style import ToastStyle
from flet_toastify.types import ToastPhase, ToastType

FAST = ToastStyle(in_duration=1, out_duration=1)


class TestShow:
    def test_show_appends_toast_and_returns_its_id(self, scheduler):
        toasts = Toasts(scheduler=scheduler)

        toast_id = toasts.show("hello")

        assert [t.id for t in toasts.toasts] == [toast_id]
        assert toasts.toasts[0].content == "hello"

    def test_show_defaults(self, scheduler):
        toasts = Toasts(scheduler=scheduler)

        toasts.show("hello")

        created = toasts.toasts[0]
        assert created.type is ToastType.INFO
        assert created.duration_ms == DEFAULT_DURATION_MS
        assert created.phase is ToastPhase.ENTERING
        assert created.style is None

    def test_show_preserves_insertion_order(self, scheduler):
        toasts = Toasts(scheduler=scheduler)

        first = toasts.show("first")
        second = toasts.show("second")

        assert [t.id for t in toasts.toasts] == [first, second]

    def test_show_at_index_inserts_in_position(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        first = toasts.show("first")
        second = toasts.show("second")

        inserted = toasts.show("between", index=1)

        assert [t.id for t in toasts.toasts] == [first, inserted, second]

    def test_show_accepts_control_content_and_per_toast_style(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        content = ft.Text("custom")
        style = ToastStyle(width=320)

        toasts.show(content, type=ToastType.WARNING, duration=0, style=style)

        created = toasts.toasts[0]
        assert created.content is content
        assert created.type is ToastType.WARNING
        assert created.duration_ms == 0
        assert created.style is style


class TestShortcuts:
    def test_shortcuts_set_type_and_return_id(self, scheduler):
        toasts = Toasts(scheduler=scheduler)

        ids = [
            toasts.info("i"),
            toasts.success("s"),
            toasts.warning("w"),
            toasts.error("e"),
        ]

        assert [t.id for t in toasts.toasts] == ids
        assert [t.type for t in toasts.toasts] == [
            ToastType.INFO,
            ToastType.SUCCESS,
            ToastType.WARNING,
            ToastType.ERROR,
        ]

    def test_shortcuts_forward_duration_and_style(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        style = ToastStyle(width=320)

        toasts.success("s", duration=1234, style=style)

        created = toasts.toasts[0]
        assert created.duration_ms == 1234
        assert created.style is style


class TestLifecycle:
    def test_full_phase_cycle_until_removal(self, scheduler):
        style = ToastStyle(in_duration=100, out_duration=50)
        toasts = Toasts(style=style, scheduler=scheduler)
        toasts.show("hello", duration=1000)

        assert toasts.toasts[0].phase is ToastPhase.ENTERING

        scheduler.advance(100)
        assert toasts.toasts[0].phase is ToastPhase.VISIBLE

        scheduler.advance(1000)
        assert toasts.toasts[0].phase is ToastPhase.LEAVING

        scheduler.advance(50)
        assert toasts.toasts == []

    def test_zero_duration_is_persistent(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        toasts.show("pinned", duration=0)

        scheduler.advance(10_000_000)

        assert len(toasts.toasts) == 1
        assert toasts.toasts[0].phase is ToastPhase.VISIBLE

    def test_per_toast_style_overrides_timing(self, scheduler):
        toasts = Toasts(style=ToastStyle(in_duration=100), scheduler=scheduler)
        toasts.show("fast", style=ToastStyle(in_duration=10), duration=0)

        scheduler.advance(10)

        assert toasts.toasts[0].phase is ToastPhase.VISIBLE


class TestDismiss:
    def test_dismiss_starts_leaving_and_removes_after_out_duration(self, scheduler):
        style = ToastStyle(in_duration=100, out_duration=50)
        toasts = Toasts(style=style, scheduler=scheduler)
        toast_id = toasts.show("hello", duration=0)
        scheduler.advance(100)

        toasts.dismiss(toast_id)

        assert toasts.toasts[0].phase is ToastPhase.LEAVING
        scheduler.advance(50)
        assert toasts.toasts == []

    def test_dismiss_cancels_pending_auto_dismiss(self, scheduler):
        style = ToastStyle(in_duration=100, out_duration=50)
        toasts = Toasts(style=style, scheduler=scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(100)

        toasts.dismiss(toast_id)
        scheduler.advance(10_000)

        assert toasts.toasts == []
        assert scheduler.pending == []

    def test_dismiss_while_entering_goes_straight_to_leaving(self, scheduler):
        style = ToastStyle(in_duration=100, out_duration=50)
        toasts = Toasts(style=style, scheduler=scheduler)
        toast_id = toasts.show("hello")

        toasts.dismiss(toast_id)

        assert toasts.toasts[0].phase is ToastPhase.LEAVING
        scheduler.advance(10_000)
        assert toasts.toasts == []

    def test_dismiss_unknown_id_is_a_noop(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        toasts.show("hello")

        toasts.dismiss("missing")

        assert len(toasts.toasts) == 1

    def test_dismiss_twice_is_idempotent(self, scheduler):
        style = ToastStyle(in_duration=100, out_duration=50)
        toasts = Toasts(style=style, scheduler=scheduler)
        toast_id = toasts.show("hello", duration=0)
        scheduler.advance(100)

        toasts.dismiss(toast_id)
        toasts.dismiss(toast_id)

        scheduler.advance(50)
        assert toasts.toasts == []


class TestPauseResume:
    def _toasts(self, scheduler):
        style = ToastStyle(in_duration=100, out_duration=50)
        return Toasts(style=style, scheduler=scheduler, clock=lambda: scheduler.now)

    def test_pause_stops_auto_dismiss(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(600)

        toasts.pause(toast_id)
        scheduler.advance(10_000)

        assert len(toasts.toasts) == 1
        assert toasts.toasts[0].paused is True
        assert toasts.toasts[0].phase is ToastPhase.VISIBLE

    def test_pause_records_remaining_time(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(600)

        toasts.pause(toast_id)

        # auto-dismiss was due at in_duration + duration = 1100
        assert toasts.toasts[0].remaining_ms == 500

    def test_resume_continues_from_remaining_time(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(600)
        toasts.pause(toast_id)
        scheduler.advance(5_000)

        toasts.resume(toast_id)

        assert toasts.toasts[0].paused is False
        scheduler.advance(499)
        assert toasts.toasts[0].phase is ToastPhase.VISIBLE
        scheduler.advance(1)
        assert toasts.toasts[0].phase is ToastPhase.LEAVING

    def test_pause_is_noop_for_persistent_toast(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("pinned", duration=0)
        scheduler.advance(100)

        toasts.pause(toast_id)

        assert toasts.toasts[0].paused is False

    def test_pause_unknown_id_is_a_noop(self, scheduler):
        toasts = self._toasts(scheduler)
        toasts.show("hello")

        toasts.pause("missing")

        assert toasts.toasts[0].paused is False

    def test_pause_twice_is_idempotent(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(600)

        toasts.pause(toast_id)
        scheduler.advance(300)
        toasts.pause(toast_id)

        assert toasts.toasts[0].remaining_ms == 500

    def test_resume_without_pause_is_a_noop(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)

        toasts.resume(toast_id)

        assert toasts.toasts[0].paused is False
        scheduler.advance(1100)
        assert toasts.toasts[0].phase is ToastPhase.LEAVING

    def test_resume_after_dismiss_does_not_reschedule(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(600)
        toasts.pause(toast_id)
        toasts.dismiss(toast_id)

        toasts.resume(toast_id)

        assert toasts.toasts[0].phase is ToastPhase.LEAVING
        assert toasts.toasts[0].paused is True
        scheduler.advance(50)
        assert toasts.toasts == []
        assert scheduler.pending == []

    def test_dismiss_while_paused_removes_the_toast(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(600)
        toasts.pause(toast_id)

        toasts.dismiss(toast_id)
        scheduler.advance(50)

        assert toasts.toasts == []

    def test_clear_while_paused_removes_everything(self, scheduler):
        toasts = self._toasts(scheduler)
        toasts.show("a", duration=1000)
        toasts.show("b", duration=1000)
        scheduler.advance(600)
        toasts.pause(toasts.toasts[0].id)

        toasts.clear()
        scheduler.advance(10_000)

        assert toasts.toasts == []
        assert scheduler.pending == []

    def test_pause_and_resume_notify_subscribers(self, scheduler):
        toasts = self._toasts(scheduler)
        toast_id = toasts.show("hello", duration=1000)
        scheduler.advance(600)
        events = []

        def listener(sender, field):
            events.append(field)

        toasts.subscribe(listener)
        toasts.pause(toast_id)
        toasts.resume(toast_id)

        assert events == ["toasts", "toasts"]


class TestClear:
    def test_clear_removes_all_toasts(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        toasts.show("a")
        toasts.show("b")

        toasts.clear()

        assert toasts.toasts == []

    def test_clear_cancels_all_pending_timers(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        toasts.show("a")
        toasts.show("b", duration=0)

        toasts.clear()

        assert scheduler.pending == []
        scheduler.advance(10_000_000)
        assert toasts.toasts == []


class TestObservability:
    def test_show_dismiss_and_clear_notify_subscribers(self, scheduler):
        toasts = Toasts(scheduler=scheduler)
        events = []

        def listener(sender, field):
            events.append(field)

        dispose = toasts.subscribe(listener)
        toast_id = toasts.show("hello")
        toasts.dismiss(toast_id)
        toasts.clear()
        dispose()

        assert events
        assert set(events) == {"toasts"}

    def test_phase_transitions_notify_subscribers(self, scheduler):
        toasts = Toasts(style=ToastStyle(in_duration=100), scheduler=scheduler)
        events = []

        def listener(sender, field):
            events.append(field)

        toasts.subscribe(listener)
        toasts.show("hello", duration=0)
        events.clear()

        scheduler.advance(100)

        assert events == ["toasts"]


class TestDefaultInstance:
    def test_toast_is_a_toasts_instance(self):
        assert isinstance(toast, Toasts)

    def test_toast_is_exported_from_package_root(self):
        assert flet_toastify.toast is toast

    def test_toasts_is_exported_from_package_root(self):
        assert flet_toastify.Toasts is Toasts


class TestAsyncioScheduler:
    async def test_default_scheduler_runs_full_cycle_on_event_loop(self):
        toasts = Toasts(style=FAST)

        toasts.show("hello", duration=10)

        assert toasts.toasts[0].phase is ToastPhase.ENTERING
        await asyncio.sleep(0.2)
        assert toasts.toasts == []

    async def test_default_scheduler_timers_are_cancellable(self):
        toasts = Toasts(style=FAST)

        toasts.show("hello", duration=10)
        toasts.clear()
        await asyncio.sleep(0.2)

        assert toasts.toasts == []
