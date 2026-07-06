<p align="center"><img src="docs/assets/logo.png" width="50%" alt="flet-toastify"></p>

**Toast-style notifications for Flet apps — declarative, animated, and fully customizable.**

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/flet-0.85.3+-00B4D8?logo=flet)
[![Docs](https://img.shields.io/badge/docs-zensical-blue)](https://brunobrown.github.io/flet-toastify)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

> Built **exclusively for Flet's declarative mode** (`@ft.component`, `@ft.observable`, hooks).
> The API follows the pattern consolidated by [react-toastify](https://github.com/fkhadra/react-toastify) and
> [sonner](https://github.com/emilkowalski/sonner): a global `toast` object callable from any
> event handler, and a single `Toaster` mounted once in the component tree.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [The global toast object](#the-global-toast-object)
  - [Toast types](#toast-types)
  - [Positions](#positions)
  - [Persistent toasts](#persistent-toasts)
  - [Dismissing programmatically](#dismissing-programmatically)
  - [Progress bar & pause on hover](#progress-bar--pause-on-hover)
  - [Custom content](#custom-content)
  - [Advanced: explicit instances](#advanced-explicit-instances)
- [Customization](#customization)
- [Migrating from NotificationCenter](#migrating-from-notificationcenter)
- [Examples](#examples)
- [Development](#development)
- [Acknowledgments](#acknowledgments)
- [Learn more](#learn-more)
- [Flet Community](#flet-community)
- [Support](#support)
- [Contributing](#contributing)

---

## Buy Me a Coffee

If you find this project useful, please consider supporting its development:

<a href="https://www.buymeacoffee.com/brunobrown">
<img src="https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-1.svg" width="200" alt="Buy Me a Coffee">
</a>

---

## Features

- **Global `toast` object** — fire a notification from any event handler with one line
- **4 semantic types** — info, success, warning, error, each with its own icon and colors
- **6 positions** — top/bottom × left/center/right, multiple toasters at once
- **Smooth animations** — entrance/exit opacity, scale, and offset, all customizable per style
- **Auto-dismiss with progress bar** — a shrinking time-left bar, colored per type
- **Pause on hover** — hovering a toast freezes its countdown; leaving resumes it
- **Selectable text** — toast messages can be selected and copied
- **Persistent toasts** — `duration=0` keeps a toast on screen until dismissed
- **Fully declarative** — state lives in an `@ft.observable` class; re-render is automatic
- **100% unit-tested core** — timers are injectable, no UI needed to test behavior

---

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

**Requirements:** Python 3.11+, Flet 0.85.3+

---

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

---

## Usage

### The global toast object

`toast` is the default `Toasts` instance exported by the package. Call it from
any event handler — the bound `Toaster` re-renders automatically:

```python
from flet_toastify import toast

toast.show("Plain message")                      # info by default
toast.info("Heads up")
toast.success("Saved!")
toast.warning("Disk almost full")
toast.error("Something went wrong")

toast_id = toast.show("Returns an id")           # every call returns the toast id
```

All methods accept the same keyword arguments:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `duration` | `int` | `5000` | Auto-dismiss timeout in milliseconds. `0` = persistent. |
| `style` | `ToastStyle` | `None` | Per-toast style override. |
| `index` | `int` | `None` | Position in the stack. `None` appends at the end. |

`show()` additionally accepts `type=ToastType.…`.

### Toast types

```python
from flet_toastify import ToastType

toast.show("message", type=ToastType.SUCCESS)
```

`ToastType`: `INFO`, `SUCCESS`, `WARNING`, `ERROR` — each resolves its own
background color, icon, icon color, text color, and progress bar color.

### Positions

```python
from flet_toastify import Position, Toaster

Toaster(position=Position.BOTTOM_CENTER)
```

`Position`: `TOP_LEFT`, `TOP_CENTER`, `TOP_RIGHT`, `BOTTOM_LEFT`,
`BOTTOM_CENTER`, `BOTTOM_RIGHT`.

### Persistent toasts

```python
toast.warning("Stays until closed", duration=0)
```

Persistent toasts show no progress bar and only leave when the user clicks
the close button or you call `dismiss(id)` / `clear()`.

### Dismissing programmatically

```python
toast_id = toast.info("Working…", duration=0)
# later:
toast.dismiss(toast_id)   # plays the exit animation, then removes
toast.clear()             # removes all toasts immediately
```

### Progress bar & pause on hover

Auto-dismiss toasts display a thin, shrinking time-left bar at the bottom of
the card (like react-toastify). Hovering the toast **pauses** the countdown
and freezes the bar; moving the pointer away **resumes** it. Message text is
selectable.

Disable the bar per style:

```python
from flet_toastify import ToastStyle

toast.show("No bar", style=ToastStyle(show_progress=False))
```

### Custom content

Anything that is a Flet control can be a toast body:

```python
toast.show(ft.Row([ft.Icon(ft.Icons.DOWNLOAD), ft.Text("Downloading…")]))
```

### Advanced: explicit instances

For multiple independent toasters — or dependency injection in tests —
create explicit `Toasts` instances and bind each `Toaster` to one
(the pattern used by notistack):

```python
from flet_toastify import Position, Toaster, Toasts, ToastStyle, ToastType

left = Toasts()
right = Toasts(ToastStyle(width=250, height=120))

# in the component tree:
Toaster(left, position=Position.TOP_LEFT)
Toaster(right, position=Position.TOP_RIGHT)

# in event handlers:
left.success("saved!")
right.show("custom", type=ToastType.WARNING, index=0, duration=0)
```

`Toaster()` without a state argument binds to the global `toast` instance.

---

## Customization

Pass a `ToastStyle` to a `Toasts` instance (affects timing and all its cards),
to a `Toaster` (affects rendering of that toaster), or to a single call via
`style=` (highest precedence for that card).

```python
import flet as ft
from flet_toastify import Toasts, ToastStyle, ToastType

style = ToastStyle(
    width=320,
    in_duration=250,
    in_offset=ft.Offset(-2, 0),
    in_offset_curve=ft.AnimationCurve.BOUNCE_OUT,
    bgcolors={ToastType.ERROR: ft.Colors.RED_900},
    text_colors={ToastType.ERROR: ft.Colors.WHITE},
)
toasts = Toasts(style)
```

### Dimensions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `height` | `int` | `70` | Card height (px). |
| `width` | `int` | `200` | Card width (px). |
| `spacing` | `int` | `10` | Gap between stacked cards (px). |
| `border_radius` | `int` | `5` | Card corner radius (px). |
| `padding` | `int` | `10` | Card inner padding (px). |

### Entrance animation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `in_duration` | `int` | `666` | Entrance duration (ms). |
| `in_opacity` | `float` | `0.0` | Starting opacity. |
| `in_opacity_curve` | `ft.AnimationCurve` | `FAST_OUT_SLOWIN` | Opacity curve. |
| `in_scale` | `float` | `0.2` | Starting scale. |
| `in_scale_curve` | `ft.AnimationCurve` | `FAST_OUT_SLOWIN` | Scale curve. |
| `in_offset` | `ft.Offset` | `Offset(0, 0)` | Starting offset. |
| `in_offset_curve` | `ft.AnimationCurve` | `FAST_OUT_SLOWIN` | Offset curve. |

### Exit animation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `out_duration` | `int` | `500` | Exit duration (ms). |
| `out_opacity` | `float` | `0.0` | Ending opacity. |
| `out_opacity_curve` | `ft.AnimationCurve` | `FAST_OUT_SLOWIN` | Opacity curve. |
| `out_scale` | `float` | `1.2` | Ending scale. |
| `out_scale_curve` | `ft.AnimationCurve` | `FAST_OUT_SLOWIN` | Scale curve. |
| `out_offset` | `ft.Offset` | `Offset(0, 0)` | Ending offset. |
| `out_offset_curve` | `ft.AnimationCurve` | `FAST_OUT_SLOWIN` | Offset curve. |
| `position_curve` | `ft.AnimationCurve` | `FAST_OUT_SLOWIN` | Curve for cards sliding to a new stack slot. |

### Progress bar

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `show_progress` | `bool` | `True` | Show the shrinking time-left bar on auto-dismiss toasts. |
| `progress_height` | `int` | `4` | Bar height (px). |
| `progress_colors` | `dict[ToastType, ft.ColorValue]` | accent colors | Bar color per type. |

### Colors & icons per type

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `bgcolors` | `dict[ToastType, ft.ColorValue]` | blue/green/amber/red 100 | Card background per type. |
| `icons` | `dict[ToastType, ft.IconData]` | info/check/warning/error outlines | Icon per type. |
| `icon_colors` | `dict[ToastType, ft.ColorValue]` | blue/green/amber/red 900 | Icon color per type. |
| `text_colors` | `dict[ToastType, ft.ColorValue]` | blue/green/amber/red 900 | Text color per type. |

Maps can be overridden **partially** — types missing from an overridden map
fall back to neutral theme colors (`PRIMARY_CONTAINER` / `PRIMARY`).

---

## Migrating from NotificationCenter

This package is a declarative rewrite of
[ositoMalvado/NotificationCenter](https://github.com/ositoMalvado/NotificationCenter).
The API changed intentionally:

| Before (imperative fork) | Now (flet-toastify) |
|--------------------------|---------------------|
| `nc = NotificationCenter(...)` + `page.add(nc)` | `Toaster(position=...)` mounted in the component tree |
| `nc.add_notification(content, "success", duration=3000)` | `toast.success("message", duration=3000)` |
| `NotificationTypes.SUCCESS.value` (loose strings) | `ToastType.SUCCESS` (typed `StrEnum`) |
| `NotificationStyle` | `ToastStyle` (frozen dataclass, typed per-type maps) |
| `alignment=ft.alignment.top_right` | `position=Position.TOP_RIGHT` |
| Imperative updates (`self.update()`, `page.run_task`) | Observable state — re-render is automatic |

---

## Examples

A full demo — global object plus two custom-styled toasters (equivalent to
the original fork demo) — lives in [`examples/main.py`](examples/main.py):

```bash
git clone https://github.com/brunobrown/flet-toastify.git
cd flet-toastify
uv sync
uv run flet run examples/main.py
```

---

## Development

```bash
# Clone and install
git clone https://github.com/brunobrown/flet-toastify.git
cd flet-toastify
uv sync

# Full quality gate: format, lint, complexity, typecheck, tests (100% coverage) and docs
uv run task quality

# Test suite only
uv run task test
```

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

## Learn more
* [Documentation](https://brunobrown.github.io/flet-toastify)

## Flet Community

Join the community to contribute or get help:

* [Discussions](https://github.com/flet-dev/flet/discussions)
* [Discord](https://discord.gg/dzWXP8SHG8)
* [X (Twitter)](https://twitter.com/fletdev)
* [Bluesky](https://bsky.app/profile/fletdev.bsky.social)
* [Email us](mailto:hello@flet.dev)

## Support

If you like this project, please give it a [GitHub star](https://github.com/brunobrown/flet-toastify) ⭐

---

## Contributing

Contributions and feedback are welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed explanation

For feedback, [open an issue](https://github.com/brunobrown/flet-toastify/issues) with your suggestions.

## Support the Project

If you find this project useful, consider giving it a star on GitHub and supporting its development:

<a href="https://www.buymeacoffee.com/brunobrown">
<img src="https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-1.svg" width="200" alt="Buy Me a Coffee">
</a>

---
## Try flet-toastify today and give your Flet app beautiful, declarative toast notifications!

<p align="center"><img src="https://github.com/user-attachments/assets/431aa05f-5fbc-4daa-9689-b9723583e25a" width="50%"></p>
<p align="center"><a href="https://www.bible.com/bible/116/PRO.16.NLT"> Commit your work to the LORD, and your plans will succeed. Proverbs 16:3</a></p>
