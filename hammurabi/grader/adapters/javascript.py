"""JavaScript solution adapter."""

from __future__ import annotations

import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun


class JavaScriptSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running JavaScript solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        """Print Node.js version information."""
        JavaScriptSolutionAdapter._run_version_command(["node", "--version"])

    def get_language_name(self) -> str:
        """Return the language identifier."""
        return "javascript"

    def get_preferred_extensions(self) -> list[str]:
        """Return file extensions for JavaScript source files."""
        return [".js"]

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to execute the JavaScript file."""
        entry_point_file = self.get_entry_point_file()
        return ["node", entry_point_file or ""]
