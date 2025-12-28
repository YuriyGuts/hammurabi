"""Data models for the grader."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from hammurabi.grader.config import ProblemConfig


@dataclass(eq=False)
class Problem:
    """A programming problem to be graded."""

    name: str
    root_dir: str
    input_filename: str = ""
    output_filename: str = ""
    solutions: list[Solution] = field(default_factory=list)
    testcases: list[TestCase] = field(default_factory=list)
    reference_solution: Solution | None = None
    config: ProblemConfig = field(default_factory=ProblemConfig)

    def __str__(self) -> str:
        """Return string representation of the problem."""
        return f"Problem: {self.name}"


@dataclass(eq=False)
class Solution:
    """A submitted solution to a problem."""

    problem: Problem
    author: str
    root_dir: str | None
    files: list[str] = field(default_factory=list)
    language: str | None = None
    run_command: str | None = None

    def __str__(self) -> str:
        """Return string representation of the solution."""
        return f"Problem: {self.problem.name}   Author: {self.author}   Language: {self.language}"

    def get_file_by_predicate(self, predicate: Callable[[str], bool]) -> str | None:
        """Return the first file matching the predicate, or None."""
        matches = self.get_files_by_predicate(predicate)
        return matches[0] if len(matches) > 0 else None

    def get_files_by_predicate(self, predicate: Callable[[str], bool]) -> list[str]:
        """Return all files matching the predicate."""
        return [file for file in self.files if predicate(file)]


@dataclass
class TestCase:
    """A single test case for a problem."""

    problem: Problem
    name: str
    input_filename: str
    correct_answer_filename: str
    score: int = 1

    def __str__(self) -> str:
        """Return string representation of the test case."""
        return (
            f"Problem: {self.problem.name}   Filename: {self.input_filename}   Score: {self.score}"
        )


@dataclass
class TestRun:
    """A single execution of a solution against a test case."""

    solution: Solution
    testcase: TestCase
    output_dir: str | None
    answer_filename: str | None
    compiler_output_filename: str | None
    stdout_filename: str | None
    stderr_filename: str | None
    result: TestRunResult | None = None
    memory_limit: int | None = None
    time_limit: float | None = None
    judge_start_time: int | None = field(default=None, repr=False)
    judge_end_time: int | None = field(default=None, repr=False)
    lean_start_time: int | None = field(default=None, repr=False)
    lean_end_time: int | None = field(default=None, repr=False)
    data: dict[str, Any] = field(default_factory=dict, repr=False)

    def __str__(self) -> str:
        """Return string representation of the test run."""
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


@dataclass(kw_only=True)
class TestRunResult:
    """Base class for test run results."""

    status_code: str
    status: str
    score: int = 0

    def __str__(self) -> str:
        """Return string representation of the result."""
        return f"[{self.status_code}] {self.status}, Score: {self.score}"

    def is_correct(self) -> bool:
        """Return True if the result indicates a correct answer."""
        return False

    def format_details(self) -> str | None:
        """Return detailed information about the result."""
        return None


@dataclass
class TestRunCorrectAnswerResult(TestRunResult):
    """Result indicating the answer was correct."""

    status_code: str = field(default="C", init=False)
    status: str = field(default="Correct Answer", init=False)

    def is_correct(self) -> bool:
        """Return True since this result indicates a correct answer."""
        return True


@dataclass
class TestRunWrongAnswerResult(TestRunResult):
    """Result indicating the answer was incorrect."""

    expected: str | None = None
    actual: str | None = None
    custom_message: str | None = None
    status_code: str = field(default="W", init=False)
    status: str = field(default="Wrong Answer", init=False)

    def format_details(self) -> str | None:
        """Return details about the expected vs actual values."""
        if self.custom_message is not None:
            return self.custom_message
        return f"Expected: {self.expected}, Actual: {self.actual}"


@dataclass
class TestRunRuntimeErrorResult(TestRunResult):
    """Result indicating a runtime error occurred."""

    message: str | None = None
    status_code: str = field(default="R", init=False)
    status: str = field(default="Runtime Error", init=False)

    def format_details(self) -> str | None:
        """Return the runtime error message."""
        return self.message


@dataclass
class TestRunFormatErrorResult(TestRunResult):
    """Result indicating the output format was invalid."""

    message: str
    status_code: str = field(default="F", init=False)
    status: str = field(default="Invalid Output Format", init=False)

    def format_details(self) -> str | None:
        """Return the format error message."""
        return self.message


@dataclass
class TestRunInternalErrorResult(TestRunResult):
    """Result indicating an internal judge error occurred."""

    exception_info: str | None = None
    status_code: str = field(default="X", init=False)
    status: str = field(default="Judge Internal Error", init=False)

    def format_details(self) -> str | None:
        """Return the exception traceback information."""
        if self.exception_info is None or len(self.exception_info) == 0:
            return super().format_details()
        return self.exception_info


@dataclass
class TestRunCompilationErrorResult(TestRunResult):
    """Result indicating compilation failed."""

    message: str | None = None
    status_code: str = field(default="E", init=False)
    status: str = field(default="Compilation Error", init=False)

    def format_details(self) -> str | None:
        """Return the compilation error message."""
        return self.message


@dataclass
class TestRunSolutionMissingResult(TestRunResult):
    """Result indicating no solution was found."""

    status_code: str = field(default="M", init=False)
    status: str = field(default="Solution Missing", init=False)


@dataclass
class TestRunUnverifiedResult(TestRunResult):
    """Result indicating the solution was not verified."""

    message: str
    status_code: str = field(default="U", init=False)
    status: str = field(default="Unverified", init=False)

    def format_details(self) -> str | None:
        """Return the reason the result was not verified."""
        return self.message


@dataclass
class TestRunTimeoutResult(TestRunResult):
    """Result indicating the solution exceeded the time limit."""

    timeout: float
    status_code: str = field(default="T", init=False)
    status: str = field(default="Timeout", init=False)

    def format_details(self) -> str | None:
        """Return a message about the timeout limit exceeded."""
        return f"Execution time exceeded the limit of {self.timeout:.2g} seconds"


@dataclass
class GraderJobScope:
    """Defines the scope of a grading job."""

    tasks: dict[Problem, dict[Solution, list[TestCase]]]
