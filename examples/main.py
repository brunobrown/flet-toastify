"""flet-toastify demo.

Two usage paths side by side:

- Simple: the global ``toast`` object with a bare ``Toaster()`` — one line
  to fire a notification from any handler.
- Advanced (equivalent to the original fork demo): two explicit ``Toasts``
  instances with custom styles mounted as separate toasters, fed by the
  Left / Right / Both buttons.

Run with::

    uv run flet run examples/main.py
"""

import random

import flet as ft

from flet_toastify import Position, Toaster, Toasts, ToastStyle, ToastType, toast

MESSAGES = [
    "Hello World",
    "What's up, bro?",
    "Superman < Goku!",
    "Proverbs 16: 3",
]

LEFT_STYLE = ToastStyle(
    in_duration=200,
    out_duration=2000,
    in_scale=0.3,
    in_scale_curve=ft.AnimationCurve.BOUNCE_OUT,
    in_opacity=0.5,
    in_offset=ft.Offset(-2, 0),
    in_offset_curve=ft.AnimationCurve.BOUNCE_OUT,
    out_scale=0.3,
    out_offset=ft.Offset(0, -4),
)

RIGHT_STYLE = ToastStyle(
    in_duration=100,
    out_duration=500,
    in_scale=2,
    in_opacity=0.5,
    width=250,
    height=120,
    in_offset=ft.Offset(0, -2),
    in_offset_curve=ft.AnimationCurve.FAST_OUT_SLOWIN,
    out_scale=1.5,
    out_opacity=0.2,
    out_offset_curve=ft.AnimationCurve.EASE_IN,
    out_offset=ft.Offset(0, 8),
)

left = Toasts(LEFT_STYLE)
right = Toasts(RIGHT_STYLE)


def random_message() -> str:
    """Return a random demo message."""
    return random.choice(MESSAGES)


def random_type() -> ToastType:
    """Return a random toast type."""
    return random.choice(list(ToastType))


@ft.component
def App():
    """Demo application component."""

    def show_left(_):
        left.show(random_message(), type=random_type())

    def show_right(_):
        # Persistent (duration=0), newest first (index=0) — close manually.
        right.show(random_message(), type=random_type(), index=0, duration=0)

    def show_both(event):
        show_left(event)
        show_right(event)

    return ft.Stack(
        expand=True,
        controls=[
            ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Text("flet-toastify demo", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Global toast object:"),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Button(
                                "Save",
                                on_click=lambda _: toast.success("File saved successfully!"),
                            ),
                            ft.Button(
                                "Fail",
                                on_click=lambda _: toast.error("Something went wrong"),
                            ),
                        ],
                    ),
                    ft.Text("Explicit Toasts instances (custom styles):"),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Button("Left", on_click=show_left),
                            ft.Button("Right", on_click=show_right),
                            ft.Button("Both", on_click=show_both),
                        ],
                    ),
                ],
            ),
            # Mounted once each, like react-toastify's <ToastContainer />.
            Toaster(position=Position.BOTTOM_CENTER),
            Toaster(left, position=Position.TOP_LEFT),
            Toaster(right, position=Position.TOP_RIGHT),
        ],
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
