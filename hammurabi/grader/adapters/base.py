"""Base adapter for running solutions."""

from __future__ import annotations

import contextlib
import shutil
import subprocess
from pathlib import Path

from hammurabi.exceptions import OutputDirectoryError
from hammurabi.exceptions import TestRunPrematureTerminationError
from hammurabi.grader import runners
from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunCompilationErrorResult
from hammurabi.grader.model import TestRunFormatErrorResult
from hammurabi.grader.model import TestRunRuntimeErrorResult
from hammurabi.grader.model import TestRunSolutionMissingResult
from hammurabi.grader.runners.base import BaseSolutionRunner
from hammurabi.utils import fileio


class BaseSolutionAdapter:
    """Base class for language-specific solution adapters."""

    solution: Solution | None
    config: ProblemConfig
    output_dir: Path

    def __init__(self, solution: Solution | None) -> None:
        self.is_compiled = False
        self.solution = solution
        if solution is not None:
            self.config = solution.problem.config
            self.output_dir = (
                Path(self.config.report_output_dir) / solution.problem.name / solution.author
            )

    def _require_solution(self) -> Solution:
        """Return the solution, raising if not set."""
        if self.solution is None:
            raise RuntimeError("Solution is required for this operation")
        return self.solution

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
            self.output_dir.rmdir()

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OutputDirectoryError("Internal error: cannot create output directory") from e

    def compile(self, testrun: TestRun) -> None:
        """Compile the solution if required."""
        solution = self._require_solution()
        compile_cmd = self.get_compile_command_line(testrun)

        if compile_cmd is not None:
            assert testrun.compiler_output_filename is not None
            with open(testrun.compiler_output_filename, "w", encoding="utf-8") as compiler_output:
                exit_code = subprocess.call(
                    compile_cmd,
                    shell=True,
                    cwd=solution.root_dir,
                    stdout=compiler_output,
                    stderr=compiler_output,
                )

            if exit_code != 0:
                compiler_output_text = fileio.read_entire_file(testrun.compiler_output_filename)
                result = TestRunCompilationErrorResult(message=compiler_output_text)
                raise TestRunPrematureTerminationError(result)

        self.is_compiled = True

    def get_compile_command_line(self, testrun: TestRun) -> str | None:
        """Return the compilation command, or None if not needed."""
        return None

    def get_entry_point_file(self) -> str | None:
        """Determine the main entry point file for the solution."""
        solution = self._require_solution()
        entry_point_file = None

        # If there's only one file, it must be the solution.
        if len(solution.files) == 1:
            entry_point_file = solution.files[0]

        # If there's more than one file, the file which has the name of the problem,
        # must be the solution.
        if entry_point_file is None:
            entry_point_file = solution.get_file_by_predicate(
                lambda f: Path(f).stem.lower() == solution.problem.name.lower()
            )

        # If that fails, try to get the first file with the name 'main' or 'program'.
        if entry_point_file is None:
            entry_point_file = solution.get_file_by_predicate(
                lambda f: Path(f).stem.lower() in ["main", "program"]
            )
        return entry_point_file

    def supply_testcase(self, testcase: TestCase) -> None:
        """Copy the test case input to the solution directory."""
        solution = self._require_solution()
        assert solution.root_dir is not None
        solution_input_path = Path(solution.root_dir) / solution.problem.input_filename
        shutil.copyfile(testcase.input_filename, solution_input_path)

    def cleanup_testcase(self, testcase: TestCase) -> None:
        """Remove the test case input from the solution directory."""
        solution = self._require_solution()
        assert solution.root_dir is not None
        solution_input_path = Path(solution.root_dir) / solution.problem.input_filename
        solution_input_path.unlink()

    def get_source_files(self) -> list[str]:
        """Return all source files for the solution."""
        solution = self._require_solution()
        return solution.get_files_by_predicate(
            lambda f: Path(f).suffix.lower() in (self.get_preferred_extensions() or [])
        )

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to run the solution."""
        solution = self._require_solution()
        return [solution.language or "", f'"{self.get_entry_point_file()}"']

    def get_run_command_line_string(self, testrun: TestRun) -> str:
        """Return the command to run the solution as a string."""
        return " ".join(self.get_run_command_line(testrun))

    def create_testrun(self, testcase: TestCase) -> TestRun:
        """Create a TestRun instance for a test case."""
        solution = self._require_solution()
        compiler_output_filename = str(self.output_dir / f"compiler_{testcase.name}.log")
        answer_filename = str(self.output_dir / f"{testcase.name}.out")
        stdout_filename = str(self.output_dir / f"{testcase.name}.stdout")
        stderr_filename = str(self.output_dir / f"{testcase.name}.stderr")
        memory_limit = self.config.limits.memory
        time_limit = self.config.limits.time.get_for_language(solution.language)

        return TestRun(
            solution=solution,
            testcase=testcase,
            output_dir=str(self.output_dir),
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
        runner_name = testrun.solution.problem.config.runner.name
        runner_class = runners.registered_runners.get(runner_name)
        if runner_class is None:
            raise ValueError(
                f"Unknown runner '{runner_name}'. "
                f"Available: {', '.join(runners.registered_runners.keys())}"
            )
        return runner_class()

    def collect_output(self, testrun: TestRun) -> None:
        """Collect the solution output after execution."""
        solution = self._require_solution()
        assert solution.root_dir is not None
        assert testrun.stderr_filename is not None
        assert testrun.answer_filename is not None

        given_answer_path = Path(solution.root_dir) / solution.problem.output_filename
        if not given_answer_path.exists():
            stderr_path = Path(testrun.stderr_filename)
            if stderr_path.stat().st_size > 0:
                error_text = fileio.read_entire_file(testrun.stderr_filename)
                result = TestRunRuntimeErrorResult(message=error_text)
            else:
                msg = f"Output file '{solution.problem.output_filename}' is empty or missing."
                result = TestRunFormatErrorResult(msg)
            raise TestRunPrematureTerminationError(result)

        shutil.move(str(given_answer_path), testrun.answer_filename)
