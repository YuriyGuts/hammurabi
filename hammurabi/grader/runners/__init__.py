"""Solution runners for executing solutions."""

import importlib
import inspect
import pkgutil

# Load all modules from the current directory.
__all__: list[str] = []

for _loader, module_name, _is_pkg in pkgutil.walk_packages(__path__):
    module = importlib.import_module("." + module_name, __name__)

    for name, value in inspect.getmembers(module):
        if name.startswith("__"):
            continue

        globals()[name] = value
        __all__ += [name]  # noqa: PLE0604 - name is always a string from inspect.getmembers
