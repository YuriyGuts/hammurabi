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
        subprocess.call("java -version", shell=True)
        subprocess.call("javac -version", shell=True)

    def get_language_name(self) -> str:
        return "java"

    def get_preferred_extensions(self) -> list[str]:
        return [".java"]

    def get_compile_command_line(self, testrun: TestRun) -> str:
        java_sources = " ".join([f'"{file}"' for file in self.get_source_files()])
        return f"javac -O -d . {java_sources}"

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
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
