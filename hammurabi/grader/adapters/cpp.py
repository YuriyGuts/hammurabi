"""C++ solution adapter."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun

if platform.system() == "Windows":
    from hammurabi.grader.adapters import windows_toolchain


class CppSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running C++ solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        """Print C++ compiler version information."""
        if platform.system() == "Windows":
            windows_toolchain.print_compiler_version()
        else:
            subprocess.call("g++ --version", shell=True)

    def get_language_name(self) -> str:
        """Return the language identifier."""
        return "cpp"

    def get_preferred_extensions(self) -> list[str]:
        """Return file extensions for C++ source files."""
        return [".cpp"]

    def get_compile_command_line(self, testrun: TestRun) -> str:
        """Return the command to compile C++ source files."""
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            return windows_toolchain.build_cpp_compile_command(
                sources=list(self.get_source_files()),
                output_path=executable_filename,
            )
        else:
            cpp_sources = " ".join([f'"{file}"' for file in self.get_source_files()])
            return f'g++ -std=c++11 -O3 {cpp_sources} -o "{executable_filename}"'

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to execute the compiled program."""
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
