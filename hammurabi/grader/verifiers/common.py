import filecmp
import sys

from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunFormatErrorResult
from hammurabi.grader.model import TestRunWrongAnswerResult


class AnswerVerifier:
    def __init__(self):
        pass

    def verify(self, testrun):
        # Use strict byte-by-byte comparison by default.
        return filecmp.cmp(
            testrun.answer_filename, testrun.testcase.correct_answer_filename, shallow=False
        )


class SpaceCharacterSeparatedSequenceVerifier(AnswerVerifier):
    def __init__(self):
        super().__init__()

    def map_input_item(self, item):
        return str(item)

    def verify(self, testrun):
        with (
            open(testrun.answer_filename) as given_answer_file,
            open(testrun.testcase.correct_answer_filename) as correct_answer_file,
        ):
            # Matching the files line-by-line.
            for correct_line in correct_answer_file.readlines():
                try:
                    given_line = given_answer_file.readline()
                except Exception:
                    exc_type, exc, tb = sys.exc_info()
                    testrun.result = TestRunFormatErrorResult(message=str(exc))
                    return False

                # Matching the space-separated tokens in both lines.
                if len(correct_line.strip()) > 0:
                    correct_items = [self.map_input_item(item) for item in correct_line.split()]
                    try:
                        given_items = [self.map_input_item(item) for item in given_line.split()]
                        if correct_items != given_items:
                            expected = '"{}"'.format(
                                " ".join([str(item) for item in correct_items])
                            )
                            actual = '"{}"'.format(" ".join([str(item) for item in given_items]))
                            testrun.result = TestRunWrongAnswerResult(
                                expected=expected, actual=actual
                            )
                            return False
                    except Exception:
                        exc_type, exc, tb = sys.exc_info()
                        testrun.result = TestRunFormatErrorResult(message=str(exc))
                        return False

            # If there's non-empty stuff remaining in the given answer file, raise an error.
            try:
                extra_line = given_answer_file.readline()
                if len(extra_line.strip()) > 0:
                    testrun.result = TestRunFormatErrorResult(
                        message="The answer file contained more information than required."
                    )
                    return False
            except Exception:
                pass

        testrun.result = TestRunCorrectAnswerResult()
        return True


class IntegerSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    def __init__(self):
        super().__init__()

    def map_input_item(self, item):
        return int(item)


class FloatSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    def __init__(self):
        super().__init__()

    def map_input_item(self, item):
        return float(item)


class WordSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    def __init__(self):
        super().__init__()
