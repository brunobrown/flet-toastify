"""Toast notifications for Flet apps, built for declarative mode.

Quick start — global ``toast`` object plus a single ``Toaster`` mounted in
the component tree, the pattern popularized by react-toastify and sonner::

    import flet as ft
    from flet_toastify import Position, Toaster, toast


    @ft.component
    def App():
        return ft.Stack(
            expand=True,
            controls=[
                ft.Button("Save", on_click=lambda _: toast.success("Saved!")),
                Toaster(position=Position.TOP_RIGHT),
            ],
        )


    ft.run(lambda page: page.render(App))

Advanced — explicit :class:`Toasts` instances for multiple toasters or
dependency injection in tests::

    left = Toasts()
    Toaster(left, position=Position.TOP_LEFT)   # in the tree
    left.success("saved!")                      # in handlers
"""

from importlib.metadata import version

from flet_toastify.components import ToastCard, Toaster
from flet_toastify.models import Toast
from flet_toastify.state import Toasts, toast
from flet_toastify.style import ToastStyle
from flet_toastify.types import Position, ToastPhase, ToastType

__version__ = version("flet-toastify")

__all__: list[str] = [
    "Position",
    "Toast",
    "ToastCard",
    "ToastPhase",
    "ToastStyle",
    "ToastType",
    "Toaster",
    "Toasts",
    "toast",
]
