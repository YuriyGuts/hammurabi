"""C solution adapter."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import TYPE_CHECKING

from hammurabi.grader.adapters.base import BaseSolutionAdapter

if TYPE_CHECKING:
    from hammurabi.grader.model import Solution
    from hammurabi.grader.model import TestRun


class CSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running C solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        if platform.system() == "Windows":
            # Just use C++ compiler on Windows.
            subprocess.call("vsvars32.bat & cl", shell=True)
        else:
            subprocess.call("LC_ALL=C LANG=C gcc --version", shell=True)

    def get_language_name(self) -> str:
        return "c"

    def get_preferred_extensions(self) -> list[str]:
        return [".c"]

    def get_compile_command_line(self, testrun: TestRun) -> str:
        c_sources = " ".join([f'"{file}"' for file in self.get_source_files()])
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            return f'vsvars32.bat & cl /Ox /EHsc {c_sources} /link /out:"{executable_filename}"'
        else:
            # LANG=C forces gcc to use ASCII instead of UTF-8,
            # so reports don't break when locale is set to UTF-8.
            return f'LC_ALL=C LANG=C gcc --std=c99 -O2 {c_sources} -o "{executable_filename}"'

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        executable_filename = self._get_executable_filename(testrun)
        if platform.system() == "Windows":
            return [executable_filename]
        else:
            return ["./" + executable_filename]

    def _get_executable_filename(self, testrun: TestRun) -> str:
        if platform.system() == "Windows":
            return os.path.abspath(
                os.path.join(testrun.solution.root_dir, testrun.solution.problem.name + ".exe")
            )
        else:
            return testrun.solution.problem.name
