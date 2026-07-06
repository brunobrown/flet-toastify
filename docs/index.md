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

## Quality

- `uv run task quality` — format, lint, complexity, typecheck and tests (100% coverage)
- `uv run task test` — test suite only
- `uv run task docs` — docstring/API Reference validation, diagrams and documentation build
