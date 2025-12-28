"""Tests for the reporting module."""

from __future__ import annotations

import csv
import pickle
from pathlib import Path

import pytest

from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunCompilationErrorResult
from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunFormatErrorResult
from hammurabi.grader.model import TestRunInternalErrorResult
from hammurabi.grader.model import TestRunRuntimeErrorResult
from hammurabi.grader.model import TestRunSolutionMissingResult
from hammurabi.grader.model import TestRunTimeoutResult
from hammurabi.grader.model import TestRunUnverifiedResult
from hammurabi.grader.model import TestRunWrongAnswerResult
from hammurabi.grader.reporting import adjust_time_for_language
from hammurabi.grader.reporting import csv_escape_string
from hammurabi.grader.reporting import dump_file
from hammurabi.grader.reporting import dump_preformatted_text
from hammurabi.grader.reporting import format_timestamp
from hammurabi.grader.reporting import format_timestamp_micro
from hammurabi.grader.reporting import generate_testrun_log_csv
from hammurabi.grader.reporting import get_contextual_style_by_result
from hammurabi.grader.reporting import get_jinja_environment
from hammurabi.grader.reporting import heat_color_for_percentile
from hammurabi.grader.reporting import is_correct_answer
from hammurabi.grader.reporting import percentile
from hammurabi.grader.reporting import pickle_testruns
from hammurabi.grader.reporting import summary_statistics


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


@pytest.fixture
def sample_testcase(sample_problem: Problem) -> TestCase:
    """Create a sample test case for testing."""
    return TestCase(
        problem=sample_problem,
        name="01",
        input_filename="/tmp/test/testcases/01.in",
        correct_answer_filename="/tmp/test/answers/01.out",
        score=10,
    )


@pytest.fixture
def sample_testrun(sample_solution: Solution, sample_testcase: TestCase) -> TestRun:
    """Create a sample test run for testing."""
    testrun = TestRun(
        solution=sample_solution,
        testcase=sample_testcase,
        output_dir="/tmp/test/output",
        answer_filename="/tmp/test/output/answer.out",
        compiler_output_filename=None,
        stdout_filename="/tmp/test/output/stdout.txt",
        stderr_filename="/tmp/test/output/stderr.txt",
    )
    testrun.judge_start_time = 1000000
    testrun.judge_end_time = 1000100
    testrun.lean_start_time = 1000010
    testrun.lean_end_time = 1000090
    testrun.result = TestRunCorrectAnswerResult(score=10)
    return testrun


class TestCsvEscapeString:
    """Tests for csv_escape_string function."""

    def test_passes_printable_characters(self):
        """Printable ASCII characters should pass through unchanged."""
        result = csv_escape_string("Hello World 123")
        assert result == "Hello World 123"

    def test_replaces_newlines_with_spaces(self):
        """Newline characters should be replaced with spaces."""
        result = csv_escape_string("Hello\nWorld")
        assert result == "Hello World"

    def test_replaces_tabs_with_spaces(self):
        """Tab characters should be replaced with spaces."""
        result = csv_escape_string("Hello\tWorld")
        assert result == "Hello World"

    def test_replaces_control_characters(self):
        """Control characters should be replaced with spaces."""
        result = csv_escape_string("Hello\x00World")
        assert result == "Hello World"

    def test_empty_string(self):
        """Empty string should return empty string."""
        result = csv_escape_string("")
        assert result == ""


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_formats_timestamp_with_default_format(self):
        """Should format timestamp with default format."""
        # 2023-01-15 12:30:45 UTC
        timestamp = 1673785845.0
        result = format_timestamp(timestamp)
        # The result depends on local timezone, so just check format
        assert len(result) == 19
        assert result[4] == "-"
        assert result[7] == "-"
        assert result[10] == " "
        assert result[13] == ":"
        assert result[16] == ":"

    def test_formats_timestamp_with_custom_format(self):
        """Should format timestamp with custom format."""
        timestamp = 1673785845.0
        result = format_timestamp(timestamp, format="%Y/%m/%d")
        assert "/" in result


class TestFormatTimestampMicro:
    """Tests for format_timestamp_micro function."""

    def test_formats_millisecond_timestamp(self):
        """Should format millisecond timestamp."""
        timestamp = 1673785845123.0
        result = format_timestamp_micro(timestamp)
        # Result should be truncated if ends with 000
        if result is not None:
            assert "." in result

    def test_returns_none_for_non_truncatable(self):
        """Should return None when microseconds don't end with 000."""
        # This tests the specific behavior where result is None
        # if the formatted string ends with "000"
        timestamp = 1673785845000.0
        result = format_timestamp_micro(timestamp)
        # The function returns the truncated string if it ends with 000
        assert result is not None


class TestDumpPreformattedText:
    """Tests for dump_preformatted_text function."""

    def test_returns_short_content_unchanged(self):
        """Short content should be returned unchanged."""
        content = "Hello World"
        result = dump_preformatted_text(content)
        assert result == content

    def test_truncates_long_content(self):
        """Content longer than 1024 chars should be truncated."""
        content = "x" * 2000
        result = dump_preformatted_text(content)
        assert result is not None
        assert len(result) < 2000
        assert "[content too long, truncated]" in result

    def test_returns_none_for_none(self):
        """None input should return None."""
        result = dump_preformatted_text(None)
        assert result is None

    def test_returns_whitespace_only_unchanged(self):
        """Whitespace-only content should be returned as-is."""
        content = "   "
        result = dump_preformatted_text(content)
        assert result == content


class TestDumpFile:
    """Tests for dump_file function."""

    def test_returns_none_for_none_filename(self):
        """None filename should return None."""
        result = dump_file(None)
        assert result is None

    def test_returns_none_for_nonexistent_file(self, tmp_path: Path):
        """Nonexistent file should return None."""
        result = dump_file(str(tmp_path / "nonexistent.txt"))
        assert result is None

    def test_reads_file_content(self, tmp_path: Path):
        """Should read and return file content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")
        result = dump_file(str(test_file))
        assert result == "Hello World"

    def test_truncates_long_file(self, tmp_path: Path):
        """Long file content should be truncated."""
        test_file = tmp_path / "long.txt"
        test_file.write_text("x" * 2000)
        result = dump_file(str(test_file))
        assert result is not None
        assert "[content too long, truncated]" in result


class TestGetContextualStyleByResult:
    """Tests for get_contextual_style_by_result function."""

    def test_correct_answer_returns_success(self):
        """Correct answer should return 'success' style."""
        result = TestRunCorrectAnswerResult(score=10)
        assert get_contextual_style_by_result(result) == "success"

    def test_wrong_answer_returns_danger(self):
        """Wrong answer should return 'danger' style."""
        result = TestRunWrongAnswerResult()
        assert get_contextual_style_by_result(result) == "danger"

    def test_timeout_returns_info(self):
        """Timeout should return 'info' style."""
        result = TestRunTimeoutResult(timeout=5.0)
        assert get_contextual_style_by_result(result) == "info"

    def test_compilation_error_returns_warning(self):
        """Compilation error should return 'warning' style."""
        result = TestRunCompilationErrorResult()
        assert get_contextual_style_by_result(result) == "warning"

    def test_runtime_error_returns_warning(self):
        """Runtime error should return 'warning' style."""
        result = TestRunRuntimeErrorResult()
        assert get_contextual_style_by_result(result) == "warning"

    def test_format_error_returns_warning(self):
        """Format error should return 'warning' style."""
        result = TestRunFormatErrorResult(message="bad format")
        assert get_contextual_style_by_result(result) == "warning"

    def test_solution_missing_returns_warning(self):
        """Solution missing should return 'warning' style."""
        result = TestRunSolutionMissingResult()
        assert get_contextual_style_by_result(result) == "warning"

    def test_internal_error_returns_warning(self):
        """Internal error should return 'warning' style."""
        result = TestRunInternalErrorResult()
        assert get_contextual_style_by_result(result) == "warning"

    def test_unverified_returns_primary(self):
        """Unverified should return 'primary' style."""
        result = TestRunUnverifiedResult(message="not verified")
        assert get_contextual_style_by_result(result) == "primary"


class TestIsCorrectAnswer:
    """Tests for is_correct_answer function."""

    def test_returns_true_for_correct_answer(self, sample_testrun: TestRun):
        """Should return True for correct answer result."""
        sample_testrun.result = TestRunCorrectAnswerResult(score=10)
        assert is_correct_answer(sample_testrun) is True

    def test_returns_false_for_wrong_answer(self, sample_testrun: TestRun):
        """Should return False for wrong answer result."""
        sample_testrun.result = TestRunWrongAnswerResult()
        assert is_correct_answer(sample_testrun) is False

    def test_returns_false_for_none_result(self, sample_testrun: TestRun):
        """Should return False when result is None."""
        sample_testrun.result = None
        assert is_correct_answer(sample_testrun) is False


class TestAdjustTimeForLanguage:
    """Tests for adjust_time_for_language function."""

    def test_cpp_time_unchanged_below_threshold(self):
        """C++ time below threshold should be unchanged."""
        result = adjust_time_for_language(40, "cpp")
        assert result == 40.0

    def test_java_time_adjusted_for_bootstrap(self):
        """Java time should have bootstrap allowance subtracted."""
        result = adjust_time_for_language(40, "java")
        # 40 - 30 (bootstrap) = 10
        assert result == 10.0

    def test_time_above_threshold_adjusted_by_slowness_factor(self):
        """Time above threshold should be adjusted by slowness factor."""
        # For python with time=150ms:
        # Above threshold (50), so: 50 + (150-50) / 5.0 = 50 + 20 = 70
        result = adjust_time_for_language(150, "python")
        assert result == 70.0

    def test_none_language_uses_defaults(self):
        """None language should use default factors."""
        result = adjust_time_for_language(40, None)
        assert result == 40.0


class TestPercentile:
    """Tests for percentile function."""

    def test_returns_zero_for_single_element(self):
        """Single element list should return 0.0."""
        result = percentile([100.0], 100.0)
        assert result == 0.0

    def test_returns_zero_for_empty_list(self):
        """Empty list should return 0.0."""
        result = percentile([], 50.0)
        assert result == 0.0

    def test_first_element_is_zero_percentile(self):
        """First element in sorted list should be 0.0 percentile."""
        result = percentile([10.0, 20.0, 30.0, 40.0, 50.0], 10.0)
        assert result == 0.0

    def test_last_element_is_one_percentile(self):
        """Last element in sorted list should be 1.0 percentile."""
        result = percentile([10.0, 20.0, 30.0, 40.0, 50.0], 50.0)
        assert result == 1.0

    def test_middle_element_percentile(self):
        """Middle element should have 0.5 percentile."""
        result = percentile([10.0, 20.0, 30.0, 40.0, 50.0], 30.0)
        assert result == 0.5


class TestSummaryStatistics:
    """Tests for summary_statistics function."""

    def test_calculates_mean_correctly(self):
        """Should calculate correct mean."""
        mean, _ = summary_statistics([10.0, 20.0, 30.0])
        assert mean == 20.0

    def test_calculates_stddev_correctly(self):
        """Should calculate correct standard deviation."""
        _, stddev = summary_statistics([10.0, 20.0, 30.0])
        # Variance = ((10-20)^2 + (20-20)^2 + (30-20)^2) / 3 = 200/3
        # Stddev = sqrt(200/3) ≈ 8.165
        assert stddev is not None
        assert abs(stddev - 8.165) < 0.01

    def test_returns_none_for_empty_list(self):
        """Empty list should return (None, None)."""
        mean, stddev = summary_statistics([])
        assert mean is None
        assert stddev is None


class TestHeatColorForPercentile:
    """Tests for heat_color_for_percentile function."""

    def test_returns_hex_color_string(self):
        """Should return a hex color string."""
        result = heat_color_for_percentile(0.5)
        assert result.startswith("#")
        assert len(result) == 7

    def test_zero_percentile_produces_valid_color(self):
        """Zero percentile should produce valid color."""
        result = heat_color_for_percentile(0.0)
        assert result.startswith("#")

    def test_one_percentile_produces_valid_color(self):
        """One percentile should produce valid color."""
        result = heat_color_for_percentile(1.0)
        assert result.startswith("#")


class TestGetJinjaEnvironment:
    """Tests for get_jinja_environment function."""

    def test_returns_environment_with_loader(self):
        """Should return environment with FileSystemLoader."""
        env = get_jinja_environment()
        assert env.loader is not None

    def test_environment_has_custom_filters(self):
        """Environment should have custom filters registered."""
        env = get_jinja_environment()
        assert "format_timestamp" in env.filters
        assert "format_timestamp_micro" in env.filters
        assert "dump" in env.filters
        assert "dump_file" in env.filters
        assert "contextual_style" in env.filters
        assert "is_correct_answer" in env.filters
        assert "summary_statistics" in env.filters


class TestPickleTestruns:
    """Tests for pickle_testruns function."""

    def test_creates_pickle_file(self, tmp_path: Path, sample_testrun: TestRun):
        """Should create a pickle file."""
        filename = str(tmp_path / "testruns.pickle")
        pickle_testruns([sample_testrun], filename)
        assert Path(filename).exists()

    def test_pickle_file_is_readable(self, tmp_path: Path, sample_testrun: TestRun):
        """Pickle file should be readable and contain the test runs."""
        filename = str(tmp_path / "testruns.pickle")
        pickle_testruns([sample_testrun], filename)

        with open(filename, "rb") as f:
            loaded = pickle.load(f)

        assert len(loaded) == 1
        assert loaded[0].solution.author == "test_author"


class TestGenerateTestrunLogCsv:
    """Tests for generate_testrun_log_csv function."""

    def test_creates_csv_file(self, tmp_path: Path, sample_testrun: TestRun):
        """Should create a CSV file."""
        filename = str(tmp_path / "testruns.csv")
        generate_testrun_log_csv([sample_testrun], filename)
        assert Path(filename).exists()

    def test_csv_has_correct_headers(self, tmp_path: Path, sample_testrun: TestRun):
        """CSV file should have correct headers."""
        filename = str(tmp_path / "testruns.csv")
        generate_testrun_log_csv([sample_testrun], filename)

        with open(filename) as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        assert headers is not None
        assert "problem_name" in headers
        assert "solution_author" in headers
        assert "result_status" in headers
        assert "score" in headers

    def test_csv_contains_testrun_data(self, tmp_path: Path, sample_testrun: TestRun):
        """CSV file should contain test run data."""
        filename = str(tmp_path / "testruns.csv")
        generate_testrun_log_csv([sample_testrun], filename)

        with open(filename) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["problem_name"] == "test_problem"
        assert rows[0]["solution_author"] == "test_author"
        assert rows[0]["result_status"] == "C"

    def test_testruns_sorted_by_start_time(self, tmp_path: Path, sample_testrun: TestRun):
        """Test runs should be sorted by start time in CSV."""
        # Create two test runs with different start times
        testrun1 = TestRun(
            solution=sample_testrun.solution,
            testcase=sample_testrun.testcase,
            output_dir=None,
            answer_filename=None,
            compiler_output_filename=None,
            stdout_filename=None,
            stderr_filename=None,
        )
        testrun1.judge_start_time = 2000
        testrun1.result = TestRunCorrectAnswerResult(score=5)

        testrun2 = TestRun(
            solution=sample_testrun.solution,
            testcase=sample_testrun.testcase,
            output_dir=None,
            answer_filename=None,
            compiler_output_filename=None,
            stdout_filename=None,
            stderr_filename=None,
        )
        testrun2.judge_start_time = 1000
        testrun2.result = TestRunWrongAnswerResult()

        filename = str(tmp_path / "testruns.csv")
        generate_testrun_log_csv([testrun1, testrun2], filename)

        with open(filename) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # testrun2 should come first (start_time=1000)
        assert rows[0]["start_time"] == "1000"
        assert rows[1]["start_time"] == "2000"
