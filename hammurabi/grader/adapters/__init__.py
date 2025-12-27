"""Language-specific solution adapters."""

from __future__ import annotations

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.adapters.c import CSolutionAdapter
from hammurabi.grader.adapters.cpp import CppSolutionAdapter
from hammurabi.grader.adapters.csharp import CSharpSolutionAdapter
from hammurabi.grader.adapters.java import JavaSolutionAdapter
from hammurabi.grader.adapters.javascript import JavaScriptSolutionAdapter
from hammurabi.grader.adapters.python import PythonSolutionAdapter
from hammurabi.grader.adapters.ruby import RubySolutionAdapter

__all__ = [
    "BaseSolutionAdapter",
    "CSolutionAdapter",
    "CppSolutionAdapter",
    "CSharpSolutionAdapter",
    "JavaSolutionAdapter",
    "JavaScriptSolutionAdapter",
    "PythonSolutionAdapter",
    "RubySolutionAdapter",
    "registered_adapters",
]

# Registry mapping language names to adapter classes
_adapters = [
    CSolutionAdapter,
    CppSolutionAdapter,
    CSharpSolutionAdapter,
    JavaSolutionAdapter,
    JavaScriptSolutionAdapter,
    PythonSolutionAdapter,
    RubySolutionAdapter,
]

registered_adapters: dict[str, type[BaseSolutionAdapter]] = {
    name: adapter
    for adapter in _adapters
    if (name := adapter(None).get_language_name()) is not None
}
