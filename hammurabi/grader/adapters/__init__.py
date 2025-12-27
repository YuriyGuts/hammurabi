import inspect
import pkgutil
import sys
import importlib


# Load all modules from current directory.
__all__ = []

for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    module = importlib.import_module("." + name, __name__)

    for name, value in inspect.getmembers(module):
        if name.startswith('__'):
            continue

        globals()[name] = value
        __all__.append(name)


# Create adapter registry.
registered_adapters = {
    cls(None).get_language_name(): cls
    for name, cls in inspect.getmembers(sys.modules[__name__])
    if isinstance(cls, type) and issubclass(cls, BaseSolutionAdapter) and cls != BaseSolutionAdapter
}
