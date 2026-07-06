# Overview

**flet-toastify** is a toast notification package for [Flet](https://flet.dev)
apps, built exclusively for **declarative mode** (`@ft.component`, `@ft.observable`, hooks).

The API follows the pattern established by libraries such as react-toastify and sonner:
a global `toast` object callable from any event handler, and a single `Toaster`
mounted in the component tree.

## Installation

```bash
uv add flet-toastify
# or
pip install flet-toastify
```

## Quick start

```python
import flet as ft
from flet_toastify import Position, Toaster, toast


@ft.component
def App():
    def on_save(_):
        toast.success("File saved successfully!", duration=3000)

    return ft.Stack(
        expand=True,
        controls=[
            ft.Column([ft.Button("Save", on_click=on_save)]),
            Toaster(position=Position.TOP_RIGHT),
        ],
    )


ft.run(lambda page: page.render(App))
```

## Advanced: explicit instances

For multiple toasters (or dependency injection in tests), create explicit
`Toasts` instances and bind each `Toaster` to one:

```python
from flet_toastify import Position, Toaster, Toasts, ToastType

left = Toasts()
right = Toasts()

# in the component tree:
Toaster(left, position=Position.TOP_LEFT)
Toaster(right, position=Position.TOP_RIGHT)

# in event handlers:
left.success("saved!")
right.show("heads up", type=ToastType.WARNING, duration=0)  # persistent
```

A full demo (global object + two custom-styled toasters) lives in
[`examples/main.py`](https://github.com/brunobrown/flet-toastify/blob/main/examples/main.py).

## Quality

- `uv run task quality` — format, lint, complexity, typecheck and tests (100% coverage)
- `uv run task test` — test suite only
- `uv run task docs` — docstring/API Reference validation, diagrams and documentation build
