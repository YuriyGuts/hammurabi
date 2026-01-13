"""C solution adapter."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun

if platform.system() == "Windows":
    from hammurabi.grader.adapters import windows_toolchain


class CSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running C solutions."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        """Print C compiler version information."""
        if platform.system() == "Windows":
            windows_toolchain.print_compiler_version()
        else:
            env = {**os.environ, "LC_ALL": "C", "LANG": "C"}
            CSolutionAdapter._run_version_command(["gcc", "--version"], env=env)

    def get_language_name(self) -> str:
        """Return the language identifier."""
        return "c"

    def get_preferred_extensions(self) -> list[str]:
        """Return file extensions for C source files."""
        return [".c"]

    def get_compile_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to compile C source files."""
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            return windows_toolchain.build_c_compile_command(
                sources=list(self.get_source_files()),
                output_path=executable_filename,
            )
        else:
            # Build argument list: `gcc --std=c99 -O2 <sources> -o <output>`.
            cmd = ["gcc", "--std=c99", "-O2"]
            cmd.extend(self.get_source_files())
            cmd.extend(["-o", executable_filename])
            return cmd

    def get_compile_env(self) -> dict[str, str] | None:
        """Return environment for compilation."""
        if platform.system() == "Windows":
            # Use MSVC environment if needed.
            return windows_toolchain.get_compile_env()
        # LANG=C forces gcc to use ASCII instead of UTF-8,
        # so reports don't break when locale is set to UTF-8.
        return {**os.environ, "LC_ALL": "C", "LANG": "C"}

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
            return str(Path(testrun.solution.root_dir) / f"{testrun.solution.problem.name}.exe")
        else:
            return testrun.solution.problem.name
