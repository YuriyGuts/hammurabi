"""Custom verifier template for problem-specific verification logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunWrongAnswerResult
from hammurabi.grader.verifiers.common import AnswerVerifier

if TYPE_CHECKING:
    from hammurabi.grader.model import TestRun


class MyCustomVerifier(AnswerVerifier):
    """Example custom verifier template."""

    def __init__(self) -> None:
        super().__init__()

    def verify(self, testrun: TestRun) -> bool:
        """Verify the answer with custom logic."""
        with open(testrun.answer_filename), open(testrun.testcase.correct_answer_filename):
            # ...
            # Read and compare stuff here.
            # ...
            something_wrong = True

            if something_wrong:
                testrun.result = TestRunWrongAnswerResult(expected="foo", actual="bar")
                return False

            testrun.result = TestRunCorrectAnswerResult()
            return True
