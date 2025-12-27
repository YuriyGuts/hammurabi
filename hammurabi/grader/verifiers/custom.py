"""Custom verifier template for problem-specific verification logic."""

from __future__ import annotations

from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunWrongAnswerResult
from hammurabi.grader.verifiers.common import AnswerVerifier


class MyCustomVerifier(AnswerVerifier):
    """Example custom verifier template."""

    def __init__(self) -> None:
        super().__init__()

    def verify(self, testrun: TestRun) -> bool:
        """Verify the answer with custom logic."""
        assert testrun.answer_filename is not None
        with (
            open(testrun.answer_filename, encoding="utf-8") as given_answer_file,
            open(testrun.testcase.correct_answer_filename, encoding="utf-8") as correct_answer_file,
        ):
            # ...
            # Read and compare stuff here.
            # ...
            _ = given_answer_file.read()
            _ = correct_answer_file.read()

            something_wrong = True

            if something_wrong:
                testrun.result = TestRunWrongAnswerResult(expected="foo", actual="bar")
                return False

            testrun.result = TestRunCorrectAnswerResult()
            return True
