"""Custom exceptions for the Hammurabi grader."""

from __future__ import annotations

from hammurabi.grader.model import TestRunResult


class SubprocessTimeoutError(Exception):
    """Raised when a subprocess exceeds its time limit."""

    def __init__(self, message: str, timeout: float, exit_code: int | None) -> None:
        super().__init__(message)
        self.timeout = timeout
        self.exit_code = exit_code


class TestRunPrematureTerminationError(Exception):
    """Raised when a test run terminates before producing output."""

    # Prevent pytest from collecting this class as a test case.
    __test__ = False

    def __init__(self, testrun_result: TestRunResult) -> None:
        super().__init__("Solution has failed before producing any answers.")
        self.result = testrun_result


class OutputDirectoryError(Exception):
    """Raised when the output directory cannot be created."""

    pass


class VerifierCreationError(Exception):
    """Raised when a verifier cannot be created."""

    pass
