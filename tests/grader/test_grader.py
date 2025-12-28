"""Unit tests for the grader module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from hammurabi.exceptions import VerifierCreationError
from hammurabi.grader import adapters
from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.config import GraderConfig
from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.grader import _create_adapter
from hammurabi.grader.grader import _create_verifier
from hammurabi.grader.grader import _fill_testruns_for_missing_solutions
from hammurabi.grader.grader import _generate_reports
from hammurabi.grader.grader import _get_scope
from hammurabi.grader.grader import _read_config
from hammurabi.grader.grader import judge_solution
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunSolutionMissingResult


@pytest.fixture
def sample_problem(tmp_path: Path) -> Problem:
    """Create a sample problem for testing."""
    problem = Problem(name="test_problem", root_dir="/tmp/test")
    problem.config = ProblemConfig()
    problem.config.verifier = "AnswerVerifier"
    problem.config.report_output_dir = str(tmp_path)
    return problem


@pytest.fixture
def sample_solution(sample_problem: Problem) -> Solution:
    """Create a sample solution for testing."""
    solution = Solution(
        problem=sample_problem,
        author="test_author",
        root_dir="/tmp/test/solutions/test_author",
        language="python",
    )
    return solution


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


class TestReadConfig:
    """Tests for the _read_config function."""

    def test_reads_config_from_args_conf(self, tmp_path: Path):
        """Should read config from the path specified in args.conf."""
        config_file = tmp_path / "grader.conf"
        config_data = {
            "locations": {
                "problem_root": "/tmp/problems",
                "report_root": "/tmp/reports",
                "report_folder_template": "testrun",
            }
        }
        config_file.write_text(json.dumps(config_data))

        args = argparse.Namespace(conf=str(config_file))
        config = _read_config(args)

        assert config.locations.problem_root == "/tmp/problems"
        assert config.locations.report_root == "/tmp/reports"

    def test_raises_error_when_config_file_not_found(self, tmp_path: Path):
        """Should raise OSError when config file doesn't exist."""
        nonexistent_config = tmp_path / "nonexistent.conf"
        args = argparse.Namespace(conf=str(nonexistent_config))

        with pytest.raises(OSError, match="Configuration file.*not found"):
            _read_config(args)


class TestGetScope:
    """Tests for the _get_scope function."""

    @pytest.fixture
    def problems_with_solutions(self, sample_problem: Problem) -> list[Problem]:
        """Create problems with solutions and testcases."""
        solution1 = Solution(sample_problem, "alice", "/tmp/alice", "python")
        solution2 = Solution(sample_problem, "bob", "/tmp/bob", "java")
        sample_problem.solutions = [solution1, solution2]

        tc1 = TestCase(sample_problem, "01", "/tmp/01.in", "/tmp/01.out", 10)
        tc2 = TestCase(sample_problem, "02", "/tmp/02.in", "/tmp/02.out", 20)
        sample_problem.testcases = [tc1, tc2]

        return [sample_problem]

    def test_returns_all_problems_when_no_filter(self, problems_with_solutions: list[Problem]):
        """Should include all problems when args.problem is None."""
        args = argparse.Namespace(problem=None, author=None, testcase=None, reference=False)
        scope = _get_scope(problems_with_solutions, args)

        assert len(scope.tasks) == 1
        assert problems_with_solutions[0] in scope.tasks

    def test_filters_problems_by_name(self, problems_with_solutions: list[Problem]):
        """Should filter problems by name when args.problem is specified."""
        args = argparse.Namespace(
            problem=["test_problem"], author=None, testcase=None, reference=False
        )
        scope = _get_scope(problems_with_solutions, args)

        assert len(scope.tasks) == 1

    def test_excludes_problems_not_in_filter(self, problems_with_solutions: list[Problem]):
        """Should exclude problems not matching the filter."""
        args = argparse.Namespace(
            problem=["other_problem"], author=None, testcase=None, reference=False
        )
        scope = _get_scope(problems_with_solutions, args)

        assert len(scope.tasks) == 0

    def test_filters_solutions_by_author(self, problems_with_solutions: list[Problem]):
        """Should filter solutions by author when args.author is specified."""
        args = argparse.Namespace(problem=None, author=["alice"], testcase=None, reference=False)
        scope = _get_scope(problems_with_solutions, args)

        problem = problems_with_solutions[0]
        solutions = list(scope.tasks[problem].keys())
        assert len(solutions) == 1
        assert solutions[0].author == "alice"

    def test_filters_testcases_by_name(self, problems_with_solutions: list[Problem]):
        """Should filter testcases by name when args.testcase is specified."""
        args = argparse.Namespace(problem=None, author=None, testcase=["01"], reference=False)
        scope = _get_scope(problems_with_solutions, args)

        problem = problems_with_solutions[0]
        solution = list(scope.tasks[problem].keys())[0]
        testcases = scope.tasks[problem][solution]
        assert len(testcases) == 1
        assert testcases[0].name == "01"

    def test_reference_mode_uses_reference_solution(self, problems_with_solutions: list[Problem]):
        """Should use reference solution when args.reference is True."""
        problem = problems_with_solutions[0]
        ref_solution = Solution(problem, "_reference", "/tmp/ref", "python")
        problem.reference_solution = ref_solution

        args = argparse.Namespace(problem=None, author=None, testcase=None, reference=True)
        scope = _get_scope(problems_with_solutions, args)

        solutions = list(scope.tasks[problem].keys())
        assert len(solutions) == 1
        assert solutions[0].author == "_reference"


class TestCreateAdapter:
    """Tests for the _create_adapter function."""

    def test_returns_base_adapter_for_none_language(self, sample_problem: Problem):
        """Should return BaseSolutionAdapter when language is None."""
        solution = Solution(sample_problem, "test", "/tmp/test", language=None)

        adapter = _create_adapter(solution)

        assert isinstance(adapter, BaseSolutionAdapter)

    def test_returns_base_adapter_for_unknown_language(self, sample_problem: Problem):
        """Should return BaseSolutionAdapter for unknown language."""
        solution = Solution(sample_problem, "test", "/tmp/test", language="unknown_lang")

        adapter = _create_adapter(solution)

        assert isinstance(adapter, BaseSolutionAdapter)

    def test_returns_registered_adapter_for_known_language(self, sample_problem: Problem):
        """Should return registered adapter for known language."""
        solution = Solution(sample_problem, "test", "/tmp/test", language="python")

        adapter = _create_adapter(solution)

        # Should get the Python adapter if registered
        expected_class = adapters.registered_adapters.get("python", BaseSolutionAdapter)
        assert isinstance(adapter, expected_class)


class TestCreateVerifier:
    """Tests for the _create_verifier function."""

    def test_returns_verifier_for_known_verifier_name(self, sample_testrun: TestRun):
        """Should return verifier instance for registered verifier name."""
        sample_testrun.solution.problem.config.verifier = "AnswerVerifier"

        verifier = _create_verifier(sample_testrun)

        assert verifier is not None

    def test_raises_error_for_unknown_verifier(self, sample_testrun: TestRun):
        """Should raise VerifierCreationError for unknown verifier."""
        sample_testrun.solution.problem.config.verifier = "UnknownVerifier"

        with pytest.raises(VerifierCreationError, match="Unknown verifier"):
            _create_verifier(sample_testrun)

    def test_error_message_lists_available_verifiers(self, sample_testrun: TestRun):
        """Error message should list available verifiers."""
        sample_testrun.solution.problem.config.verifier = "UnknownVerifier"

        with pytest.raises(VerifierCreationError, match="Available:"):
            _create_verifier(sample_testrun)


class TestFillTestrunsForMissingSolutions:
    """Tests for the _fill_testruns_for_missing_solutions function."""

    def test_returns_same_list_when_no_missing_solutions(self, sample_testrun: TestRun):
        """Should return same list when all authors have solutions for all problems."""
        testruns = [sample_testrun]

        result = _fill_testruns_for_missing_solutions(testruns)

        assert len(result) == 1

    def test_adds_testruns_for_missing_solutions(self, sample_problem: Problem):
        """Should add placeholder testruns for missing solutions."""
        # Create two problems
        problem1 = sample_problem
        problem2 = Problem(name="problem2", root_dir="/tmp/problem2")
        problem2.config = ProblemConfig()

        # Create testcases for both problems
        tc1 = TestCase(problem1, "01", "/tmp/01.in", "/tmp/01.out", 10)
        tc2 = TestCase(problem2, "01", "/tmp/01.in", "/tmp/01.out", 10)
        problem1.testcases = [tc1]
        problem2.testcases = [tc2]

        # Create solutions
        solution1 = Solution(problem1, "alice", "/tmp/alice", "python")
        solution2 = Solution(problem2, "bob", "/tmp/bob", "python")

        # Create testruns - alice solved problem1, bob solved problem2
        testrun1 = TestRun(solution1, tc1, None, None, None, None, None)
        testrun1.result = TestRunCorrectAnswerResult(score=10)
        testrun1.record_judge_start_time()
        testrun1.record_lean_start_time()
        testrun1.record_lean_end_time()
        testrun1.record_judge_end_time()

        testrun2 = TestRun(solution2, tc2, None, None, None, None, None)
        testrun2.result = TestRunCorrectAnswerResult(score=10)
        testrun2.record_judge_start_time()
        testrun2.record_lean_start_time()
        testrun2.record_lean_end_time()
        testrun2.record_judge_end_time()

        result = _fill_testruns_for_missing_solutions([testrun1, testrun2])

        # Should have 4 testruns: original 2 + 2 placeholders
        assert len(result) == 4

    def test_placeholder_testruns_have_solution_missing_result(self, sample_problem: Problem):
        """Placeholder testruns should have TestRunSolutionMissingResult."""
        problem1 = sample_problem
        problem2 = Problem(name="problem2", root_dir="/tmp/problem2")
        problem2.config = ProblemConfig()

        tc1 = TestCase(problem1, "01", "/tmp/01.in", "/tmp/01.out", 10)
        tc2 = TestCase(problem2, "01", "/tmp/01.in", "/tmp/01.out", 10)
        problem1.testcases = [tc1]
        problem2.testcases = [tc2]

        solution1 = Solution(problem1, "alice", "/tmp/alice", "python")
        solution2 = Solution(problem2, "bob", "/tmp/bob", "python")

        testrun1 = TestRun(solution1, tc1, None, None, None, None, None)
        testrun1.result = TestRunCorrectAnswerResult(score=10)
        testrun1.record_judge_start_time()
        testrun1.record_lean_start_time()
        testrun1.record_lean_end_time()
        testrun1.record_judge_end_time()

        testrun2 = TestRun(solution2, tc2, None, None, None, None, None)
        testrun2.result = TestRunCorrectAnswerResult(score=10)
        testrun2.record_judge_start_time()
        testrun2.record_lean_start_time()
        testrun2.record_lean_end_time()
        testrun2.record_judge_end_time()

        result = _fill_testruns_for_missing_solutions([testrun1, testrun2])

        # Find the placeholder testruns
        placeholders = [tr for tr in result if isinstance(tr.result, TestRunSolutionMissingResult)]
        assert len(placeholders) == 2

    def test_empty_list_returns_empty(self):
        """Empty list should return empty list."""
        result = _fill_testruns_for_missing_solutions([])

        assert result == []


class TestJudgeSolution:
    """Tests for the judge_solution function."""

    def test_returns_empty_list_when_adapter_creation_fails(self, sample_problem: Problem):
        """Should return empty list when adapter creation fails."""
        # Create a solution with no files, which will cause adapter issues
        solution = Solution(sample_problem, "test", None, language="nonexistent_lang")
        testcases: list[TestCase] = []

        result = judge_solution(solution, testcases)

        assert result == []

    def test_returns_testruns_for_each_testcase(self, sample_problem: Problem):
        """Should return a testrun for each testcase (when adapter works)."""
        # This test verifies the function signature and return type
        solution = Solution(sample_problem, "test", None, language=None)
        testcases: list[TestCase] = []

        # With no testcases, should return empty list
        result = judge_solution(solution, testcases)

        assert isinstance(result, list)


class TestGenerateReports:
    """Tests for the _generate_reports function."""

    def test_creates_pickle_file(self, tmp_path: Path, sample_testrun: TestRun):
        """Should create pickle file."""
        config = GraderConfig()
        config.report_output_dir = str(tmp_path)

        _generate_reports(config, [sample_testrun])

        assert (tmp_path / "testruns.pickle").exists()

    def test_creates_csv_file(self, tmp_path: Path, sample_testrun: TestRun):
        """Should create CSV file."""
        config = GraderConfig()
        config.report_output_dir = str(tmp_path)

        _generate_reports(config, [sample_testrun])

        assert (tmp_path / "testruns.csv").exists()

    def test_creates_html_reports(self, tmp_path: Path, sample_testrun: TestRun):
        """Should create HTML report files."""
        config = GraderConfig()
        config.report_output_dir = str(tmp_path)

        _generate_reports(config, [sample_testrun])

        assert (tmp_path / "report-full.html").exists()
        assert (tmp_path / "report-matrix.html").exists()
        assert (tmp_path / "report-heatmap.html").exists()

    def test_handles_empty_testruns_list(self, tmp_path: Path):
        """Should handle empty testruns list gracefully."""
        config = GraderConfig()
        config.report_output_dir = str(tmp_path)

        # Should not raise an exception
        _generate_reports(config, [])

        # Files should still be created (possibly empty)
        assert (tmp_path / "testruns.pickle").exists()
        assert (tmp_path / "testruns.csv").exists()
