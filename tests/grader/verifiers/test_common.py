"""Tests for the common verifiers module."""

from __future__ import annotations

from pathlib import Path

import pytest

from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunFormatErrorResult
from hammurabi.grader.model import TestRunWrongAnswerResult
from hammurabi.grader.verifiers.common import AnswerVerifier
from hammurabi.grader.verifiers.common import FloatSequenceVerifier
from hammurabi.grader.verifiers.common import IntegerSequenceVerifier
from hammurabi.grader.verifiers.common import SpaceCharacterSeparatedSequenceVerifier
from hammurabi.grader.verifiers.common import WordSequenceVerifier


@pytest.fixture
def sample_problem() -> Problem:
    """Create a sample problem for testing."""
    problem = Problem(name="test_problem", root_dir="/tmp/test")
    problem.config = ProblemConfig()
    return problem


@pytest.fixture
def sample_solution(sample_problem: Problem) -> Solution:
    """Create a sample solution for testing."""
    return Solution(
        problem=sample_problem,
        author="test_author",
        root_dir="/tmp/test/solutions/test_author",
        language="python",
    )


def create_testrun(
    sample_solution: Solution,
    tmp_path: Path,
    given_answer: str,
    correct_answer: str,
) -> TestRun:
    """Create a test run with the given and correct answer files."""
    answer_file = tmp_path / "answer.out"
    answer_file.write_text(given_answer)

    correct_file = tmp_path / "correct.out"
    correct_file.write_text(correct_answer)

    testcase = TestCase(
        problem=sample_solution.problem,
        name="01",
        input_filename=str(tmp_path / "input.in"),
        correct_answer_filename=str(correct_file),
        score=10,
    )

    return TestRun(
        solution=sample_solution,
        testcase=testcase,
        output_dir=str(tmp_path),
        answer_filename=str(answer_file),
        compiler_output_filename=None,
        stdout_filename=None,
        stderr_filename=None,
    )


class TestAnswerVerifier:
    """Tests for the AnswerVerifier class."""

    def test_returns_true_for_identical_files(self, sample_solution: Solution, tmp_path: Path):
        """Should return True when files are byte-for-byte identical."""
        content = "Hello World\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = AnswerVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_returns_false_for_different_files(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when files differ."""
        testrun = create_testrun(sample_solution, tmp_path, "Hello World\n", "Hello Universe\n")
        verifier = AnswerVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_returns_false_for_different_whitespace(
        self, sample_solution: Solution, tmp_path: Path
    ):
        """Should return False when files differ only in whitespace."""
        testrun = create_testrun(sample_solution, tmp_path, "Hello World\n", "Hello World \n")
        verifier = AnswerVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_returns_false_for_missing_newline(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when trailing newline differs."""
        testrun = create_testrun(sample_solution, tmp_path, "Hello World", "Hello World\n")
        verifier = AnswerVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_empty_files_are_equal(self, sample_solution: Solution, tmp_path: Path):
        """Empty files should be considered equal."""
        testrun = create_testrun(sample_solution, tmp_path, "", "")
        verifier = AnswerVerifier()

        result = verifier.verify(testrun)

        assert result is True


class TestSpaceCharacterSeparatedSequenceVerifier:
    """Tests for the SpaceCharacterSeparatedSequenceVerifier class."""

    def test_returns_true_for_identical_tokens(self, sample_solution: Solution, tmp_path: Path):
        """Should return True when tokens match exactly."""
        content = "hello world\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True
        assert isinstance(testrun.result, TestRunCorrectAnswerResult)

    def test_ignores_extra_whitespace_between_tokens(
        self, sample_solution: Solution, tmp_path: Path
    ):
        """Should ignore extra whitespace between tokens."""
        testrun = create_testrun(sample_solution, tmp_path, "hello   world\n", "hello world\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_ignores_leading_and_trailing_whitespace(
        self, sample_solution: Solution, tmp_path: Path
    ):
        """Should ignore leading and trailing whitespace on lines."""
        testrun = create_testrun(sample_solution, tmp_path, "  hello world  \n", "hello world\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_returns_false_for_different_tokens(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when tokens differ."""
        testrun = create_testrun(sample_solution, tmp_path, "hello world\n", "hello universe\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False
        assert isinstance(testrun.result, TestRunWrongAnswerResult)

    def test_wrong_answer_includes_expected_and_actual(
        self, sample_solution: Solution, tmp_path: Path
    ):
        """Wrong answer result should include expected and actual values."""
        testrun = create_testrun(sample_solution, tmp_path, "foo bar\n", "hello world\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        verifier.verify(testrun)

        assert isinstance(testrun.result, TestRunWrongAnswerResult)
        assert testrun.result.expected == '"hello world"'
        assert testrun.result.actual == '"foo bar"'

    def test_returns_false_for_missing_tokens(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when answer has fewer tokens."""
        testrun = create_testrun(sample_solution, tmp_path, "hello\n", "hello world\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_returns_false_for_extra_tokens(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when answer has extra tokens."""
        testrun = create_testrun(sample_solution, tmp_path, "hello world extra\n", "hello world\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_multiline_verification(self, sample_solution: Solution, tmp_path: Path):
        """Should verify multiple lines correctly."""
        content = "line one\nline two\nline three\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_returns_format_error_for_extra_lines(self, sample_solution: Solution, tmp_path: Path):
        """Should return format error when answer has extra lines."""
        testrun = create_testrun(sample_solution, tmp_path, "hello\nextra line\n", "hello\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False
        assert isinstance(testrun.result, TestRunFormatErrorResult)
        assert "more information" in testrun.result.message

    def test_empty_lines_consume_given_lines(self, sample_solution: Solution, tmp_path: Path):
        """Empty lines in correct answer consume but don't compare given lines."""
        # Empty line in correct file skips comparison but still reads from given
        # So both files must have matching structure including empty lines
        testrun = create_testrun(sample_solution, tmp_path, "hello\n\nworld\n", "hello\n\nworld\n")
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_map_input_item_returns_string(self):
        """map_input_item should return the input as a string."""
        verifier = SpaceCharacterSeparatedSequenceVerifier()

        result = verifier.map_input_item("hello")

        assert result == "hello"
        assert isinstance(result, str)


class TestIntegerSequenceVerifier:
    """Tests for the IntegerSequenceVerifier class."""

    def test_returns_true_for_matching_integers(self, sample_solution: Solution, tmp_path: Path):
        """Should return True when integer sequences match."""
        content = "1 2 3\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = IntegerSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_ignores_leading_zeros(self, sample_solution: Solution, tmp_path: Path):
        """Should ignore leading zeros in integers."""
        testrun = create_testrun(sample_solution, tmp_path, "001 002\n", "1 2\n")
        verifier = IntegerSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_returns_false_for_different_integers(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when integers differ."""
        testrun = create_testrun(sample_solution, tmp_path, "1 2 3\n", "1 2 4\n")
        verifier = IntegerSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_returns_format_error_for_non_integer(self, sample_solution: Solution, tmp_path: Path):
        """Should return format error when answer contains non-integer."""
        testrun = create_testrun(sample_solution, tmp_path, "1 two 3\n", "1 2 3\n")
        verifier = IntegerSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False
        assert isinstance(testrun.result, TestRunFormatErrorResult)

    def test_handles_negative_integers(self, sample_solution: Solution, tmp_path: Path):
        """Should correctly compare negative integers."""
        content = "-1 -2 -3\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = IntegerSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_handles_large_integers(self, sample_solution: Solution, tmp_path: Path):
        """Should correctly compare large integers."""
        content = "123456789012345678901234567890\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = IntegerSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_map_input_item_returns_int(self):
        """map_input_item should convert string to int."""
        verifier = IntegerSequenceVerifier()

        result = verifier.map_input_item("42")

        assert result == 42
        assert isinstance(result, int)

    def test_map_input_item_raises_for_non_integer(self):
        """map_input_item should raise ValueError for non-integer string."""
        verifier = IntegerSequenceVerifier()

        with pytest.raises(ValueError, match="invalid literal"):
            verifier.map_input_item("not_an_int")


class TestFloatSequenceVerifier:
    """Tests for the FloatSequenceVerifier class."""

    def test_returns_true_for_matching_floats(self, sample_solution: Solution, tmp_path: Path):
        """Should return True when float sequences match."""
        content = "1.5 2.5 3.5\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = FloatSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_returns_false_for_different_floats(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when floats differ."""
        testrun = create_testrun(sample_solution, tmp_path, "1.5 2.5\n", "1.5 2.6\n")
        verifier = FloatSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_returns_format_error_for_non_float(self, sample_solution: Solution, tmp_path: Path):
        """Should return format error when answer contains non-float."""
        testrun = create_testrun(sample_solution, tmp_path, "1.5 abc\n", "1.5 2.5\n")
        verifier = FloatSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False
        assert isinstance(testrun.result, TestRunFormatErrorResult)

    def test_handles_scientific_notation(self, sample_solution: Solution, tmp_path: Path):
        """Should handle scientific notation."""
        content = "1e-5 2.5e10\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = FloatSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_handles_negative_floats(self, sample_solution: Solution, tmp_path: Path):
        """Should correctly compare negative floats."""
        content = "-1.5 -2.5\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = FloatSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_integer_and_float_representations(self, sample_solution: Solution, tmp_path: Path):
        """Integer and float representations of same value should match."""
        testrun = create_testrun(sample_solution, tmp_path, "1.0 2.0\n", "1 2\n")
        verifier = FloatSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_map_input_item_returns_float(self):
        """map_input_item should convert string to float."""
        verifier = FloatSequenceVerifier()

        result = verifier.map_input_item("3.14")

        assert result == 3.14
        assert isinstance(result, float)

    def test_map_input_item_raises_for_non_float(self):
        """map_input_item should raise ValueError for non-float string."""
        verifier = FloatSequenceVerifier()

        with pytest.raises(ValueError, match="could not convert"):
            verifier.map_input_item("not_a_float")


class TestWordSequenceVerifier:
    """Tests for the WordSequenceVerifier class."""

    def test_returns_true_for_matching_words(self, sample_solution: Solution, tmp_path: Path):
        """Should return True when word sequences match."""
        content = "hello world\n"
        testrun = create_testrun(sample_solution, tmp_path, content, content)
        verifier = WordSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is True

    def test_case_sensitive(self, sample_solution: Solution, tmp_path: Path):
        """Word comparison should be case-sensitive."""
        testrun = create_testrun(sample_solution, tmp_path, "Hello World\n", "hello world\n")
        verifier = WordSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_returns_false_for_different_words(self, sample_solution: Solution, tmp_path: Path):
        """Should return False when words differ."""
        testrun = create_testrun(sample_solution, tmp_path, "foo bar\n", "hello world\n")
        verifier = WordSequenceVerifier()

        result = verifier.verify(testrun)

        assert result is False

    def test_map_input_item_returns_string(self):
        """map_input_item should return the input as a string."""
        verifier = WordSequenceVerifier()

        result = verifier.map_input_item("hello")

        assert result == "hello"
        assert isinstance(result, str)
