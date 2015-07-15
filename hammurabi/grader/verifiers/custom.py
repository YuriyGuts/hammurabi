# Place your custom verifier classes here, or create a dedicated .py file in this folder.

from hammurabi.grader.model import *
from hammurabi.grader.verifiers.common import AnswerVerifier


class MyCustomVerifier(AnswerVerifier):
    def __init__(self):
        super(MyCustomVerifier, self).__init__()

    def verify(self, testrun):
        with open(testrun.answer_filename, "r") as given_answer_file:
            with open(testrun.testcase.correct_answer_filename, "r") as correct_answer_file:
                # ...
                # Read and compare stuff here.
                # ...
                something_wrong = True

                if something_wrong:
                    testrun.result = TestRunWrongAnswerResult(expected="foo", actual="bar")
                    return False

                testrun.result = TestRunCorrectAnswerResult()
                return True
