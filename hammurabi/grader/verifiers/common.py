"""Common answer verification classes."""

from __future__ import annotations

import filecmp
import sys
from typing import TYPE_CHECKING
from typing import Any

from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunFormatErrorResult
from hammurabi.grader.model import TestRunWrongAnswerResult

if TYPE_CHECKING:
    from hammurabi.grader.model import TestRun


class AnswerVerifier:
    """Byte-by-byte file comparison verifier."""

    def __init__(self) -> None:
        pass

    def verify(self, testrun: TestRun) -> bool:
        """Verify the answer using strict byte-by-byte comparison."""
        return filecmp.cmp(
            testrun.answer_filename, testrun.testcase.correct_answer_filename, shallow=False
        )


class SpaceCharacterSeparatedSequenceVerifier(AnswerVerifier):
    """Verifier for space-separated value sequences."""

    def __init__(self) -> None:
        super().__init__()

    def map_input_item(self, item: str) -> Any:
        """Map an input item to its compared type."""
        return str(item)

    def verify(self, testrun: TestRun) -> bool:
        """Verify by comparing space-separated tokens line by line."""
        with (
            open(testrun.answer_filename) as given_answer_file,
            open(testrun.testcase.correct_answer_filename) as correct_answer_file,
        ):
            # Matching the files line-by-line.
            for correct_line in correct_answer_file.readlines():
                try:
                    given_line = given_answer_file.readline()
                except Exception:
                    _exc_type, exc, _tb = sys.exc_info()
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
                        _exc_type, exc, _tb = sys.exc_info()
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
    """Verifier for integer sequences."""

    def __init__(self) -> None:
        super().__init__()

    def map_input_item(self, item: str) -> int:
        return int(item)


class FloatSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    """Verifier for floating-point sequences."""

    def __init__(self) -> None:
        super().__init__()

    def map_input_item(self, item: str) -> float:
        return float(item)


class WordSequenceVerifier(SpaceCharacterSeparatedSequenceVerifier):
    """Verifier for word sequences (same as base, for explicitness)."""

    def __init__(self) -> None:
        super().__init__()
