import filecmp
import sys

from hammurabi.grader.model import *


class AnswerVerifier(object):
    def __init__(self):
        pass

    def verify(self, testrun):
        # Use strict byte-by-byte comparison by default.
        return filecmp.cmp(testrun.answer_filename, testrun.testcase.correct_answer_filename, shallow=False)


class SpaceCharacterSeparatedSequenceVerifier(AnswerVerifier):
    def __init__(self):
        super(SpaceCharacterSeparatedSequenceVerifier, self).__init__()

    def map_input_item(self, item):
        return str(item)

    def verify(self, testrun):
        with open(testrun.answer_filename, "r") as given_answer_file:
            with open(testrun.testcase.correct_answer_filename, "r") as correct_answer_file:
                for correct_line in correct_answer_file.readlines():
                    try:
                        given_line = given_answer_file.readline()
                    except:
                        exc_type, exc, tb = sys.exc_info()
                        testrun.result = TestRunFormatErrorResult(message=exc.message)
                        return False

                    if len(correct_line.strip()) > 0:
                        correct_items = [self.map_input_item(item) for item in correct_line.split()]
                        try:
                            given_items = [self.map_input_item(item) for item in given_line.split()]
                            if correct_items != given_items:
                                testrun.result = TestRunWrongAnswerResult(expected=correct_items, actual=given_items)
                                return False
                        except:
                            exc_type, exc, tb = sys.exc_info()
                            testrun.result = TestRunFormatErrorResult(message=exc.message)
                            return False

        testrun.result = TestRunCorrectAnswerResult()
        return True


class IntegerSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    def __init__(self):
        super(IntegerSequenceVerifier, self).__init__()

    def map_input_item(self, item):
        return int(item)


class FloatSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    def __init__(self):
        super(FloatSequenceVerifier, self).__init__()

    def map_input_item(self, item):
        return float(item)


class WordSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    def __init__(self):
        super(WordSequenceVerifier, self).__init__()
