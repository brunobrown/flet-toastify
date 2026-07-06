---
icon: lucide/network
---

# Architecture

## Overview

`flet-toastify` is a toast notification package for Flet apps,
written exclusively for Flet 0.85+ **declarative mode**.

The design separates state from UI: toast state lives in an
`@ft.observable` class outside the component tree, and the UI is an
`@ft.component` function that simply reflects that state. Triggering a
toast from any event handler automatically re-renders the `Toaster`.

## Layers

- **Facade** (`flet_toastify/__init__.py`): the global `toast` object — a
  default `Toasts` instance exported at module level — with
  `show/info/success/warning/error/dismiss/clear` (react-toastify/sonner
  pattern).
- **State** (`state.py`): `Toasts` (`@ft.observable`) — the source of
  truth; manages the toast list, auto-dismiss and phase transitions
  with cancellable `asyncio` timers.
- **Domain** (`types.py`, `models.py`): `ToastType`, `ToastPhase`,
  `Position` (StrEnum) and the immutable `Toast` model.
- **Style** (`style.py`): `ToastStyle` — dimensions, in/out animations
  and per-type color/icon maps, with resolution and fallback.
- **UI** (`components.py`): `ToastCard` and `Toaster`
  (`@ft.component`) — thin layer; position/style logic extracted into pure,
  testable functions.

## Toast lifecycle

Every toast goes through a simple state machine:

`ENTERING → VISIBLE → LEAVING → (removed from the list)`

Transitions are driven by state (`Toasts`), never by the UI. Card
enter/exit animations are derived from the current phase plus the active
`ToastStyle`.

## Dependencies

- **Flet 0.85.3+** — the only runtime dependency.
- Ruff, Ty, Lizard and Pytest for quality gates (`uv run task quality`).
- Zensical and mkdocstrings for documentation (`uv run task docs`).

## Principles

- **TDD**: every behavior starts from a test (red-green-refactor);
  minimum 100% coverage on the core.
- **Clean Code**: small functions, cyclomatic complexity ≤ 10, intentional
  naming.
- **Declarative only**: `page.add()`, `page.update()`, `self.update()` and
  control subclassing for UI are forbidden.

## Diagrams

See [Diagrams](diagrams.md) (manually curated) and
[Generated diagrams](generated/index.md) (generated from source with
`uv run task docs-diagrams`).
