"""Ruby solution adapter."""

from __future__ import annotations

import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun


class RubySolutionAdapter(BaseSolutionAdapter):
    """Adapter for running Ruby solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        """Print Ruby interpreter version information."""
        subprocess.call(["ruby", "--version"])

    def get_language_name(self) -> str:
        """Return the language identifier."""
        return "ruby"

    def get_preferred_extensions(self) -> list[str]:
        """Return file extensions for Ruby source files."""
        return [".rb"]

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to execute the Ruby script."""
        entry_point_file = self.get_entry_point_file()
        return ["ruby", entry_point_file or ""]
