"""Java solution adapter."""

from __future__ import annotations

import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun
from hammurabi.utils import fileio


class JavaSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running Java solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        """Print Java compiler and runtime version information."""
        JavaSolutionAdapter._run_version_command(["java", "-version"])
        JavaSolutionAdapter._run_version_command(["javac", "-version"])

    def get_language_name(self) -> str:
        """Return the language identifier."""
        return "java"

    def get_preferred_extensions(self) -> list[str]:
        """Return file extensions for Java source files."""
        return [".java"]

    def get_compile_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to compile Java source files."""
        # Build argument list: javac -O -d . <sources>
        cmd = ["javac", "-O", "-d", "."]
        cmd.extend(self.get_source_files())
        return cmd

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to execute the compiled Java class."""
        entry_point_file = self.get_entry_point_file()
        if entry_point_file is None:
            return ["java", ""]

        package_name = fileio.grep_value_from_file(
            entry_point_file, r"package\s+([^\s;]+);", group_num=1
        )
        class_name = fileio.grep_value_from_file(
            entry_point_file, r"class\s+(\w+)[^\w]+", group_num=1
        )

        if package_name is not None:
            class_name = f"{package_name}.{class_name}"

        return ["java", class_name or ""]
