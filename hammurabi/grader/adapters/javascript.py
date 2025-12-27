"""JavaScript solution adapter."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from hammurabi.grader.adapters.base import BaseSolutionAdapter

if TYPE_CHECKING:
    from hammurabi.grader.model import Solution
    from hammurabi.grader.model import TestRun


class JavaScriptSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running JavaScript solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        subprocess.call("node --version", shell=True)

    def get_language_name(self) -> str:
        return "javascript"

    def get_preferred_extensions(self) -> list[str]:
        return [".js"]

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        entry_point_file = self.get_entry_point_file()
        return ["node", f'"{entry_point_file}"']
