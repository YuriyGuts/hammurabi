"""Base adapter for running solutions."""

from __future__ import annotations

import contextlib
import errno
import os
import shutil
import subprocess
from typing import TYPE_CHECKING

from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunCompilationErrorResult
from hammurabi.grader.model import TestRunFormatErrorResult
from hammurabi.grader.model import TestRunRuntimeErrorResult
from hammurabi.grader.model import TestRunSolutionMissingResult
from hammurabi.grader.runners import *  # noqa: F403  # Dynamic plugin lookup via globals()
from hammurabi.utils import fileio
from hammurabi.utils.exceptions import OutputDirectoryError
from hammurabi.utils.exceptions import TestRunPrematureTerminationError

if TYPE_CHECKING:
    from hammurabi.grader.model import Solution
    from hammurabi.grader.model import TestCase
    from hammurabi.grader.runners.base import BaseSolutionRunner


class BaseSolutionAdapter:
    """Base class for language-specific solution adapters."""

    def __init__(self, solution: Solution | None) -> None:
        self.is_compiled = False
        self.solution = solution
        if solution is not None:
            self.config = solution.problem.config
            self.output_dir = os.path.join(
                self.config.report_output_dir, self.solution.problem.name, self.solution.author
            )

    @staticmethod
    def describe() -> None:
        """Print version information for the language runtime."""
        pass

    def get_language_name(self) -> str | None:
        """Return the language identifier."""
        return None

    def get_preferred_extensions(self) -> list[str] | None:
        """Return file extensions associated with this language."""
        return None

    def prepare(self) -> None:
        """Prepare the adapter for running solutions."""
        self.clean_output()

    def clean_output(self) -> None:
        """Clean and recreate the output directory."""
        with contextlib.suppress(OSError):
            os.removedirs(self.output_dir)

        try:
            os.makedirs(self.output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise OutputDirectoryError("Internal error: cannot create output directory") from e

    def compile(self, testrun: TestRun) -> None:
        """Compile the solution if required."""
        compile_cmd = self.get_compile_command_line(testrun)

        if compile_cmd is not None:
            with open(
                testrun.compiler_output_filename, "w", encoding="utf-8"
            ) as compiler_output_file:
                exit_code = subprocess.call(
                    compile_cmd,
                    shell=True,
                    cwd=self.solution.root_dir,
                    stdout=compiler_output_file,
                    stderr=compiler_output_file,
                )

            if exit_code != 0:
                compiler_output = fileio.read_entire_file(testrun.compiler_output_filename)
                result = TestRunCompilationErrorResult(message=compiler_output)
                raise TestRunPrematureTerminationError(result)

        self.is_compiled = True

    def get_compile_command_line(self, testrun: TestRun) -> str | None:
        """Return the compilation command, or None if not needed."""
        return None

    def get_entry_point_file(self) -> str | None:
        """Determine the main entry point file for the solution."""
        entry_point_file = None

        # If there's only one file, it must be the solution.
        if len(self.solution.files) == 1:
            entry_point_file = self.solution.files[0]

        # If there's more than one file, the file which has the name of the problem,
        # must be the solution.
        if entry_point_file is None:
            entry_point_file = self.solution.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower()
                == self.solution.problem.name.lower()
            )

        # If that fails, try to get the first file with the name 'main' or 'program'.
        if entry_point_file is None:
            entry_point_file = self.solution.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower() in ["main", "program"]
            )
        return entry_point_file

    def supply_testcase(self, testcase: TestCase) -> None:
        """Copy the test case input to the solution directory."""
        solution_input_filename = os.path.join(
            self.solution.root_dir, self.solution.problem.input_filename
        )
        shutil.copyfile(testcase.input_filename, solution_input_filename)

    def cleanup_testcase(self, testcase: TestCase) -> None:
        """Remove the test case input from the solution directory."""
        solution_input_filename = os.path.join(
            self.solution.root_dir, self.solution.problem.input_filename
        )
        os.remove(solution_input_filename)

    def get_source_files(self) -> list[str]:
        """Return all source files for the solution."""
        return self.solution.get_files_by_predicate(
            lambda f: os.path.splitext(f)[1].lower() in (self.get_preferred_extensions() or [])
        )

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to run the solution."""
        return [self.solution.language or "", f'"{self.get_entry_point_file()}"']

    def get_run_command_line_string(self, testrun: TestRun) -> str:
        """Return the command to run the solution as a string."""
        return " ".join(self.get_run_command_line(testrun))

    def create_testrun(self, testcase: TestCase) -> TestRun:
        """Create a TestRun instance for a test case."""
        compiler_output_filename = os.path.join(self.output_dir, f"compiler_{testcase.name}.log")
        answer_filename = os.path.join(self.output_dir, testcase.name + ".out")
        stdout_filename = os.path.join(self.output_dir, testcase.name + ".stdout")
        stderr_filename = os.path.join(self.output_dir, testcase.name + ".stderr")
        memory_limit = self.config.limits.memory
        time_limit = self.config.limits.time.get_for_language(self.solution.language)

        return TestRun(
            solution=self.solution,
            testcase=testcase,
            output_dir=self.output_dir,
            compiler_output_filename=compiler_output_filename,
            answer_filename=answer_filename,
            stdout_filename=stdout_filename,
            stderr_filename=stderr_filename,
            memory_limit=memory_limit,
            time_limit=time_limit,
        )

    def run(self, testrun: TestRun) -> None:
        """Run the solution for a test case."""
        if self.get_entry_point_file() is None:
            result = TestRunSolutionMissingResult()
            raise TestRunPrematureTerminationError(result)

        if not self.is_compiled:
            self.compile(testrun)

        try:
            self.supply_testcase(testrun.testcase)
            cmd = self.get_run_command_line_string(testrun)
            runner = self.create_runner(testrun, cmd)
            runner.run(testrun, cmd)
        finally:
            self.cleanup_testcase(testrun.testcase)

        self.collect_output(testrun)

    def create_runner(self, testrun: TestRun, cmd: str) -> BaseSolutionRunner:
        """Create the appropriate runner for the solution."""
        runner_class = testrun.solution.problem.config.runner.name
        runner = globals()[runner_class]
        return runner()

    def collect_output(self, testrun: TestRun) -> None:
        """Collect the solution output after execution."""
        given_answer_filename = os.path.join(
            self.solution.root_dir, self.solution.problem.output_filename
        )
        if not os.path.exists(given_answer_filename):
            if os.path.getsize(testrun.stderr_filename) > 0:
                error_text = fileio.read_entire_file(testrun.stderr_filename)
                result = TestRunRuntimeErrorResult(message=error_text)
            else:
                msg = f"Output file '{self.solution.problem.output_filename}' is empty or missing."
                result = TestRunFormatErrorResult(msg)
            raise TestRunPrematureTerminationError(result)

        shutil.move(given_answer_filename, testrun.answer_filename)
