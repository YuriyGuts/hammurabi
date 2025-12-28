"""Base runner for executing solutions."""

from __future__ import annotations

from hammurabi.grader.model import TestRun


class BaseSolutionRunner:
    """Base class for solution runners."""

    def __init__(self) -> None:
        pass

    def run(self, testrun: TestRun, cmd: str) -> None:
        """Run a solution command for a test run."""
        pass
