"""C++ solution adapter."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun


class CppSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running C++ solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        if platform.system() == "Windows":
            subprocess.call("vsvars32.bat & cl", shell=True)
        else:
            subprocess.call("g++ --version", shell=True)

    def get_language_name(self) -> str:
        return "cpp"

    def get_preferred_extensions(self) -> list[str]:
        return [".cpp"]

    def get_compile_command_line(self, testrun: TestRun) -> str:
        cpp_sources = " ".join([f'"{file}"' for file in self.get_source_files()])
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            return f'vsvars32.bat & cl /Ox /EHsc {cpp_sources} /link /out:"{executable_filename}"'
        else:
            return f'g++ -std=c++11 -O3 {cpp_sources} -o "{executable_filename}"'

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        executable_filename = self._get_executable_filename(testrun)
        if platform.system() == "Windows":
            return [executable_filename]
        else:
            return ["./" + executable_filename]

    def _get_executable_filename(self, testrun: TestRun) -> str:
        if platform.system() == "Windows":
            assert testrun.solution.root_dir is not None
            exe_path = Path(testrun.solution.root_dir) / f"{testrun.solution.problem.name}.exe"
            return str(exe_path.resolve())
        else:
            return testrun.solution.problem.name
