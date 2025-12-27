"""Python solution adapter."""

from __future__ import annotations

import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun


class PythonSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running Python solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        subprocess.call("python --version", shell=True)

    def get_language_name(self) -> str:
        return "python"

    def get_preferred_extensions(self) -> list[str]:
        return [".py"]

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        entry_point_file = self.get_entry_point_file()
        return ["python", f'"{entry_point_file}"']
