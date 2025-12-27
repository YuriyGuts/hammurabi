# Place your custom verifier classes here, or create a dedicated .py file in this folder.

from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunWrongAnswerResult
from hammurabi.grader.verifiers.common import AnswerVerifier


class MyCustomVerifier(AnswerVerifier):
    def __init__(self):
        super().__init__()

    def verify(self, testrun):
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
