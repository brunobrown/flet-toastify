<h1 align="center">flet-toastify</h1>

<p align="center"><img src="assets/logo.png" width="300" alt="flet-toastify"></p>

**Toast-style notifications for Flet apps — declarative, animated, and fully customizable.**

flet-toastify is a toast notification package for [Flet](https://flet.dev) apps, built
exclusively for **declarative mode** (`@ft.component`, `@ft.observable`, hooks). The API
follows the pattern established by react-toastify and sonner: a global `toast` object
callable from any event handler, and a single `Toaster` mounted once in the component
tree. It provides:

- **Global `toast` object** — fire a notification from any handler with one line
- **4 semantic types** — info, success, warning, error, each with its own icon and colors
- **6 positions** — top/bottom × left/center/right, multiple toasters at once
- **Smooth animations** — entrance/exit opacity, scale, and offset, customizable per style
- **Auto-dismiss progress bar** — a shrinking time-left bar, colored per type
- **Pause on hover** — hovering freezes the countdown; leaving resumes it
- **Selectable text** — toast messages can be selected and copied
- **Persistent toasts** — `duration=0` keeps a toast on screen until dismissed
- **100% unit-tested core** — timers are injectable; no UI needed to test behavior

## Requirements

| Component | Minimum Version |
|-----------|-----------------|
| Python    | 3.11+           |
| Flet      | 0.85.3+         |

## Installation

```bash
# Using UV (recommended)
uv add flet-toastify

# Using pip
pip install flet-toastify
```

```bash
# From GitHub (latest development version)
uv add flet-toastify@git+https://github.com/brunobrown/flet-toastify.git

# or

pip install git+https://github.com/brunobrown/flet-toastify.git
```

## Quick Start

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
            # mounted once, like react-toastify's <ToastContainer />
            Toaster(position=Position.TOP_RIGHT),
        ],
    )


ft.run(lambda page: page.render(App))
```

!!! note
    `Toaster` must be mounted **once** inside a `ft.Stack` (usually at the root).
    Firing toasts never requires touching the component tree again — the observable
    state re-renders the `Toaster` automatically.

Auto-dismiss toasts display a shrinking time-left progress bar (colored per
toast type) by default — disable it with `ToastStyle(show_progress=False)`.
Hovering a toast pauses its countdown (bar freezes); moving the pointer away
resumes it. Message text is selectable.

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

## Architecture

The package separates state from UI — see [Architecture](architecture/index.md)
and the [API Reference](reference/api.md) for details:

```
flet_toastify
│
├── toast              # Global facade — default Toasts instance
├── state.Toasts       # @ft.observable — list, timers, pause/resume
├── models.Toast       # Immutable value object (id, content, type, phase)
├── style.ToastStyle   # Dimensions, animations, per-type colors/icons
├── types              # ToastType, ToastPhase, Position (StrEnum)
└── components         # Toaster + ToastCard (@ft.component, thin glue)
```

## Examples

A full demo — global object plus two custom-styled toasters — lives in
[`examples/main.py`](https://github.com/brunobrown/flet-toastify/blob/main/examples/main.py):

```bash
git clone https://github.com/brunobrown/flet-toastify.git
cd flet-toastify
uv sync
uv run flet run examples/main.py
```

## Quality

- `uv run task quality` — format, lint, complexity, typecheck, tests (100% coverage) and docs
- `uv run task test` — test suite only
- `uv run task docs` — docstring/API Reference validation, diagrams and documentation build

---

## Acknowledgments

flet-toastify started as a fork of
[NotificationCenter](https://github.com/ositoMalvado/NotificationCenter) by
[Julián Perez (ositoMalvado)](https://github.com/ositoMalvado) — thank you for
the original idea and implementation. The default styles and animations pay
homage to the original widget.

API design inspired by [react-toastify](https://github.com/fkhadra/react-toastify),
[sonner](https://github.com/emilkowalski/sonner),
[react-hot-toast](https://github.com/timolins/react-hot-toast), and
[notistack](https://github.com/iamhosseindhv/notistack).

---

## Contributing

Contributions and feedback are welcome!

1. Fork the [repository](https://github.com/brunobrown/flet-toastify)
2. Create a feature branch
3. Submit a pull request with a detailed explanation

For bugs or suggestions, [open an issue](https://github.com/brunobrown/flet-toastify/issues). Join the community on [Discord](https://discord.gg/dzWXP8SHG8).

---

## Support the Project

If you find this project useful, consider giving it a [star on GitHub](https://github.com/brunobrown/flet-toastify) and supporting its development:

<a href="https://www.buymeacoffee.com/brunobrown">
<img src="https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-1.svg" width="200" alt="Buy Me a Coffee">
</a>

[:fontawesome-brands-github: GitHub](https://github.com/brunobrown) · [:fontawesome-brands-x-twitter: X](https://x.com/BrunoBrown86) · [:fontawesome-brands-linkedin: LinkedIn](https://linkedin.com/in/bruno-brown-29418167/)

---

## Try **flet-toastify** today and give your Flet apps beautiful toast notifications!

---

<p align="center"><img src="assets/proverbs.png" width="50%" alt="Proverbs 16:3"></p>
<p align="center"><a href="https://www.bible.com/bible/116/PRO.16.NLT">Commit your work to the LORD, and your plans will succeed. Proverbs 16:3</a></p>
