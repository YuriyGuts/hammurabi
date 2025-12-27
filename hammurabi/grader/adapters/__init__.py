"""Language-specific solution adapters."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hammurabi.grader.adapters.base import BaseSolutionAdapter

# Load all modules from the current directory.
__all__: list[str] = []

for _loader, module_name, _is_pkg in pkgutil.walk_packages(__path__):
    module = importlib.import_module("." + module_name, __name__)

    for name, value in inspect.getmembers(module):
        if name.startswith("__"):
            continue

        globals()[name] = value
        __all__ += [name]  # noqa: PLE0604 - name is always a string from inspect.getmembers


# Create adapter registry.
# BaseSolutionAdapter is loaded dynamically above, so we get it from globals
_base_adapter = globals().get("BaseSolutionAdapter")
registered_adapters: dict[str, type[BaseSolutionAdapter]] = {
    cls(None).get_language_name(): cls
    for name, cls in inspect.getmembers(sys.modules[__name__])
    if isinstance(cls, type)
    and _base_adapter
    and issubclass(cls, _base_adapter)
    and cls != _base_adapter
}
