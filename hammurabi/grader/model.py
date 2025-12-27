"""Data models for the grader."""
# ruff: noqa: PLR0913 - Allow many arguments for model classes

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from hammurabi.grader.config import ProblemConfig


class Problem:
    """A programming problem to be graded."""

    # Type annotations for attributes set after init
    config: ProblemConfig
    input_filename: str
    output_filename: str

    def __init__(
        self,
        name: str,
        root_dir: str,
        input_filename: str | None = None,
        output_filename: str | None = None,
        solutions: list[Solution] | None = None,
        testcases: list[TestCase] | None = None,
        reference_solution: Solution | None = None,
        config: ProblemConfig | None = None,
    ) -> None:
        self.name = name
        self.root_dir = root_dir
        if input_filename is not None:
            self.input_filename = input_filename
        if output_filename is not None:
            self.output_filename = output_filename
        self.solutions = solutions if solutions is not None else []
        self.testcases = testcases if testcases is not None else []
        self.reference_solution = reference_solution
        if config is not None:
            self.config = config

    def __str__(self) -> str:
        return f"Problem: {self.name}"


class Solution:
    """A submitted solution to a problem."""

    def __init__(
        self,
        problem: Problem,
        author: str,
        root_dir: str | None,
        files: list[str] | None = None,
        language: str | None = None,
        run_command: str | None = None,
    ) -> None:
        self.problem = problem
        self.author = author
        self.root_dir = root_dir
        self.files = files if files is not None else []
        self.language = language
        self.run_command = run_command

    def __str__(self) -> str:
        return f"Problem: {self.problem.name}   Author: {self.author}   Language: {self.language}"

    def get_file_by_predicate(self, predicate: Callable[[str], bool]) -> str | None:
        """Return the first file matching the predicate, or None."""
        matches = self.get_files_by_predicate(predicate)
        return matches[0] if len(matches) > 0 else None

    def get_files_by_predicate(self, predicate: Callable[[str], bool]) -> list[str]:
        """Return all files matching the predicate."""
        return [file for file in self.files if predicate(file)]


class TestCase:
    """A single test case for a problem."""

    def __init__(
        self,
        problem: Problem,
        name: str,
        input_filename: str,
        correct_answer_filename: str,
        score: int = 1,
    ) -> None:
        self.problem = problem
        self.name = name
        self.input_filename = input_filename
        self.correct_answer_filename = correct_answer_filename
        self.score = score

    def __str__(self) -> str:
        return (
            f"Problem: {self.problem.name}   Filename: {self.input_filename}   Score: {self.score}"
        )


class TestRun:
    """A single execution of a solution against a test case."""

    def __init__(
        self,
        solution: Solution,
        testcase: TestCase,
        output_dir: str | None,
        answer_filename: str | None,
        compiler_output_filename: str | None,
        stdout_filename: str | None,
        stderr_filename: str | None,
        result: TestRunResult | None = None,
        memory_limit: int | None = None,
        time_limit: float | None = None,
    ) -> None:
        self.solution = solution
        self.testcase = testcase
        self.output_dir = output_dir
        self.compiler_output_filename = compiler_output_filename
        self.answer_filename = answer_filename
        self.stdout_filename = stdout_filename
        self.stderr_filename = stderr_filename
        self.result = result
        self.judge_start_time: int | None = None
        self.judge_end_time: int | None = None
        self.lean_start_time: int | None = None
        self.lean_end_time: int | None = None
        self.memory_limit = memory_limit
        self.time_limit = time_limit
        self.data: dict[str, Any] = {}

    def __str__(self) -> str:
        return (
            f"Solution: {self.solution.problem.name} / {self.solution.author}, "
            f"Result: {self.result}"
        )

    def record_judge_start_time(self) -> None:
        """Record the start time of the judging process."""
        self.judge_start_time = self._get_timestamp()

    def record_judge_end_time(self) -> None:
        """Record the end time of the judging process."""
        self.judge_end_time = self._get_timestamp()

    def record_lean_start_time(self) -> None:
        """Record the start time of the actual solution execution."""
        self.lean_start_time = self._get_timestamp()

    def record_lean_end_time(self) -> None:
        """Record the end time of the actual solution execution."""
        self.lean_end_time = self._get_timestamp()

    def get_judge_elapsed_milliseconds(self) -> int:
        """Return total elapsed time including judge overhead."""
        if self.judge_end_time is None or self.judge_start_time is None:
            return 0
        return self.judge_end_time - self.judge_start_time

    def get_lean_elapsed_milliseconds(self) -> int:
        """Return elapsed time for just the solution execution."""
        if self.lean_start_time is None or self.lean_end_time is None:
            return 0
        return self.lean_end_time - self.lean_start_time

    def _get_timestamp(self) -> int:
        """Return current time in milliseconds."""
        return int(round(time.time() * 1000))


class TestRunResult:
    """Base class for test run results."""

    def __init__(self, status_code: str, status: str, score: int = 0) -> None:
        self.status_code = status_code
        self.status = status
        self.score = score

    def __str__(self) -> str:
        return f"[{self.status_code}] {self.status}, Score: {self.score}"

    def is_correct(self) -> bool:
        """Return True if the result indicates a correct answer."""
        return False

    def format_details(self) -> str | None:
        """Return detailed information about the result."""
        return None


class TestRunCorrectAnswerResult(TestRunResult):
    """Result indicating the answer was correct."""

    def __init__(self) -> None:
        super().__init__("C", "Correct Answer")

    def is_correct(self) -> bool:
        return True


class TestRunWrongAnswerResult(TestRunResult):
    """Result indicating the answer was incorrect."""

    def __init__(
        self,
        expected: str | None = None,
        actual: str | None = None,
        custom_message: str | None = None,
    ) -> None:
        super().__init__("W", "Wrong Answer")
        self.expected = expected
        self.actual = actual
        self.custom_message = custom_message

    def format_details(self) -> str | None:
        if self.custom_message is not None:
            return self.custom_message
        return f"Expected: {self.expected}, Actual: {self.actual}"


class TestRunRuntimeErrorResult(TestRunResult):
    """Result indicating a runtime error occurred."""

    def __init__(self, message: str | None) -> None:
        super().__init__("R", "Runtime Error")
        self.message = message

    def format_details(self) -> str | None:
        return self.message


class TestRunFormatErrorResult(TestRunResult):
    """Result indicating the output format was invalid."""

    def __init__(self, message: str) -> None:
        super().__init__("F", "Invalid Output Format")
        self.message = message

    def format_details(self) -> str | None:
        return self.message


class TestRunInternalErrorResult(TestRunResult):
    """Result indicating an internal judge error occurred."""

    def __init__(self, exception_info: str | None) -> None:
        super().__init__("X", "Judge Internal Error")
        self.exception_info = exception_info

    def format_details(self) -> str | None:
        if self.exception_info is None or len(self.exception_info) == 0:
            return super().format_details()
        return self.exception_info


class TestRunCompilationErrorResult(TestRunResult):
    """Result indicating compilation failed."""

    def __init__(self, message: str | None) -> None:
        super().__init__("E", "Compilation Error")
        self.message = message

    def format_details(self) -> str | None:
        return self.message


class TestRunSolutionMissingResult(TestRunResult):
    """Result indicating no solution was found."""

    def __init__(self) -> None:
        super().__init__("M", "Solution Missing")


class TestRunUnverifiedResult(TestRunResult):
    """Result indicating the solution was not verified."""

    def __init__(self, message: str) -> None:
        super().__init__("U", "Unverified")
        self.message = message

    def format_details(self) -> str | None:
        return self.message


class TestRunTimeoutResult(TestRunResult):
    """Result indicating the solution exceeded the time limit."""

    def __init__(self, timeout: float) -> None:
        super().__init__("T", "Timeout")
        self.timeout = timeout

    def format_details(self) -> str | None:
        return f"Execution time exceeded the limit of {self.timeout:.2g} seconds"


class GraderJobScope:
    """Defines the scope of a grading job."""

    def __init__(self, tasks: dict[Problem, dict[Solution, list[TestCase]]]) -> None:
        self.tasks = tasks
