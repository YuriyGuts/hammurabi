import importlib
import inspect
import pkgutil
import sys

# Load all modules from current directory.
__all__ = []

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
registered_adapters = {
    cls(None).get_language_name(): cls
    for name, cls in inspect.getmembers(sys.modules[__name__])
    if isinstance(cls, type)
    and _base_adapter
    and issubclass(cls, _base_adapter)
    and cls != _base_adapter
}
