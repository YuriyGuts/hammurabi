"""Ruby solution adapter."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from hammurabi.grader.adapters.base import BaseSolutionAdapter

if TYPE_CHECKING:
    from hammurabi.grader.model import Solution
    from hammurabi.grader.model import TestRun


class RubySolutionAdapter(BaseSolutionAdapter):
    """Adapter for running Ruby solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        subprocess.call("ruby --version", shell=True)

    def get_language_name(self) -> str:
        return "ruby"

    def get_preferred_extensions(self) -> list[str]:
        return [".rb"]

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        entry_point_file = self.get_entry_point_file()
        return ["ruby", f'"{entry_point_file}"']
