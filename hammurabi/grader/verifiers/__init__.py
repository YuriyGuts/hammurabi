"""Answer verifiers for checking solution output."""

from __future__ import annotations

import importlib.util
import inspect
import logging
from pathlib import Path

from hammurabi.grader.verifiers.common import AnswerVerifier
from hammurabi.grader.verifiers.common import FloatSequenceVerifier
from hammurabi.grader.verifiers.common import IntegerSequenceVerifier
from hammurabi.grader.verifiers.common import SpaceCharacterSeparatedSequenceVerifier
from hammurabi.grader.verifiers.common import WordSequenceVerifier
from hammurabi.grader.verifiers.custom import MyCustomVerifier

__all__ = [
    "AnswerVerifier",
    "FloatSequenceVerifier",
    "IntegerSequenceVerifier",
    "SpaceCharacterSeparatedSequenceVerifier",
    "WordSequenceVerifier",
    "MyCustomVerifier",
    "registered_verifiers",
    "load_custom_verifiers",
]

# Registry mapping verifier names to classes
registered_verifiers: dict[str, type[AnswerVerifier]] = {
    "AnswerVerifier": AnswerVerifier,
    "FloatSequenceVerifier": FloatSequenceVerifier,
    "IntegerSequenceVerifier": IntegerSequenceVerifier,
    "SpaceCharacterSeparatedSequenceVerifier": SpaceCharacterSeparatedSequenceVerifier,
    "WordSequenceVerifier": WordSequenceVerifier,
    "MyCustomVerifier": MyCustomVerifier,
}


def load_custom_verifiers(verifiers_dir: Path) -> None:
    """
    Load custom verifier classes from a directory.

    Scans the given directory for Python files and registers any classes
    that inherit from AnswerVerifier.

    Parameters
    ----------
    verifiers_dir
        Path to the directory containing custom verifier modules.
    """
    if not verifiers_dir.is_dir():
        return

    for module_path in verifiers_dir.glob("*.py"):
        if module_path.name.startswith("_"):
            continue

        if module_path.stem == "common.py":
            continue

        module_name = f"hammurabi_custom_verifiers.{module_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            logging.warning("Failed to load custom verifier from %s", module_path, exc_info=True)
            continue

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, AnswerVerifier) and obj is not AnswerVerifier:
                registered_verifiers[name] = obj
