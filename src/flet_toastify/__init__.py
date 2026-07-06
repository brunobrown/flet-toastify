"""Toast notifications for Flet apps, built for declarative mode.

Usage follows the pattern popularized by react-toastify/sonner::

    from flet_toastify import toast, Toaster

    toast.success("File saved!")        # from any event handler
    Toaster()                           # mounted once in the component tree
"""

from importlib.metadata import version

from flet_toastify.state import Toasts, toast

__version__ = version("flet-toastify")

__all__: list[str] = ["Toasts", "toast"]
