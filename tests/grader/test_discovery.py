"""Tests for the discovery module."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from hammurabi.grader.config import GraderConfig
from hammurabi.grader.discovery import discover_problems
from hammurabi.grader.discovery import extension_to_language_map


class TestExtensionToLanguageMap:
    """Tests for the extension_to_language_map module variable."""

    def test_contains_common_extensions(self):
        """The map should contain common programming language extensions."""
        assert ".py" in extension_to_language_map
        assert ".java" in extension_to_language_map
        assert ".cpp" in extension_to_language_map
        assert ".c" in extension_to_language_map
        assert ".js" in extension_to_language_map

    def test_python_extension_maps_to_python(self):
        """Python extension should map to python language."""
        assert "python" in extension_to_language_map[".py"]

    def test_java_extension_maps_to_java(self):
        """Java extension should map to java language."""
        assert "java" in extension_to_language_map[".java"]


class TestDiscoverProblems:
    """Tests for the discover_problems function."""

    @pytest.fixture
    def grader_config(self, tmp_path: Path) -> GraderConfig:
        """Create a grader config pointing to tmp_path."""
        config = GraderConfig()
        config.problem_root_dir = str(tmp_path)
        return config

    @pytest.fixture
    def problem_directory(self, tmp_path: Path) -> Path:
        """Create a complete problem directory structure."""
        problem_dir = tmp_path / "problem1"
        problem_dir.mkdir()

        # Create testcases
        testcases_dir = problem_dir / "testcases"
        testcases_dir.mkdir()
        (testcases_dir / "01.in").write_text("input 1")
        (testcases_dir / "02.in").write_text("input 2")

        # Create answers
        answers_dir = problem_dir / "answers"
        answers_dir.mkdir()
        (answers_dir / "01.out").write_text("output 1")
        (answers_dir / "02.out").write_text("output 2")

        # Create solutions
        solutions_dir = problem_dir / "solutions"
        solutions_dir.mkdir()

        author_dir = solutions_dir / "alice"
        author_dir.mkdir()
        (author_dir / "solution.py").write_text("print('hello')")

        # Create problem.yaml
        config = {"verifier": "AnswerVerifier"}
        (problem_dir / "problem.yaml").write_text(yaml.dump(config))

        return tmp_path

    def test_discovers_problems(self, grader_config: GraderConfig, problem_directory: Path):
        """Should discover problems in the problem root directory."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert len(result) == 1
        assert result[0].name == "problem1"

    def test_problem_has_testcases(self, grader_config: GraderConfig, problem_directory: Path):
        """Discovered problems should have their test cases populated."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert len(result[0].testcases) == 2

    def test_problem_has_solutions(self, grader_config: GraderConfig, problem_directory: Path):
        """Discovered problems should have their solutions populated."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert len(result[0].solutions) == 1
        assert result[0].solutions[0].author == "alice"

    def test_problem_has_correct_root_dir(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Discovered problems should have the correct root directory."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert "problem1" in result[0].root_dir

    def test_problem_has_default_input_output_filenames(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Problems should have input/output filenames based on problem name."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert result[0].input_filename == "problem1.in"
        assert result[0].output_filename == "problem1.out"

    def test_extracts_reference_solution(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Should extract _reference solution and remove it from solutions list."""
        # Add a reference solution
        ref_dir = problem_directory / "problem1" / "solutions" / "_reference"
        ref_dir.mkdir()
        (ref_dir / "solution.py").write_text("print('reference')")

        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert result[0].reference_solution is not None
        assert result[0].reference_solution.author == "_reference"
        # Reference should not be in regular solutions
        assert all(s.author != "_reference" for s in result[0].solutions)

    def test_multiple_problems(self, grader_config: GraderConfig, tmp_path: Path):
        """Should discover multiple problems."""
        for name in ["problem_a", "problem_b", "problem_c"]:
            problem_dir = tmp_path / name
            problem_dir.mkdir()
            (problem_dir / "testcases").mkdir()
            (problem_dir / "answers").mkdir()
            (problem_dir / "solutions").mkdir()
            (problem_dir / "problem.yaml").write_text("{}")

        grader_config.problem_root_dir = str(tmp_path)

        result = discover_problems(grader_config)

        assert len(result) == 3
        names = {p.name for p in result}
        assert names == {"problem_a", "problem_b", "problem_c"}

    def test_empty_problem_root(self, grader_config: GraderConfig, tmp_path: Path):
        """Should return empty list when no problems exist."""
        grader_config.problem_root_dir = str(tmp_path)

        result = discover_problems(grader_config)

        assert result == []

    def test_problem_config_merged_with_grader_config(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Problem config should be merged with grader config."""
        # Update problem.yaml with custom verifier
        config = {"verifier": "CustomVerifier"}
        (problem_directory / "problem1" / "problem.yaml").write_text(yaml.dump(config))

        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert result[0].config.verifier == "CustomVerifier"

    def test_custom_testcase_scores_from_config(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Test case scores from problem config should be applied."""
        config = {"testcase_score": {"01": 10, "02": 20}}
        (problem_directory / "problem1" / "problem.yaml").write_text(yaml.dump(config))

        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        testcases = result[0].testcases
        tc_01 = next(tc for tc in testcases if tc.name == "01")
        tc_02 = next(tc for tc in testcases if tc.name == "02")
        assert tc_01.score == 10
        assert tc_02.score == 20

    def test_solution_language_is_detected(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Solutions should have their language detected from file extensions."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert result[0].solutions[0].language == "python"

    def test_solution_files_are_discovered(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Solutions should have their source files discovered."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        assert len(result[0].solutions[0].files) == 1
        assert result[0].solutions[0].files[0].endswith(".py")

    def test_testcases_sorted_by_name(self, grader_config: GraderConfig, problem_directory: Path):
        """Test cases should be returned in sorted order."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        names = [tc.name for tc in result[0].testcases]
        assert names == ["01", "02"]

    def test_testcase_has_correct_filenames(
        self, grader_config: GraderConfig, problem_directory: Path
    ):
        """Test cases should have correct input and answer filenames."""
        grader_config.problem_root_dir = str(problem_directory)

        result = discover_problems(grader_config)

        tc = result[0].testcases[0]
        assert tc.input_filename.endswith("01.in")
        assert tc.correct_answer_filename.endswith("01.out")

    def test_problem_without_config_uses_defaults(
        self, grader_config: GraderConfig, tmp_path: Path
    ):
        """Problem without problem.yaml should use default configuration."""
        # Create a problem directory WITHOUT problem.yaml
        problem_dir = tmp_path / "no_config_problem"
        problem_dir.mkdir()

        testcases_dir = problem_dir / "testcases"
        testcases_dir.mkdir()
        (testcases_dir / "01.in").write_text("test input")

        answers_dir = problem_dir / "answers"
        answers_dir.mkdir()
        (answers_dir / "01.out").write_text("test output")

        solutions_dir = problem_dir / "solutions"
        solutions_dir.mkdir()
        author_dir = solutions_dir / "test_author"
        author_dir.mkdir()
        (author_dir / "solution.py").write_text("print('test')")

        # No problem.yaml created!

        grader_config.problem_root_dir = str(tmp_path)

        result = discover_problems(grader_config)

        assert len(result) == 1
        assert result[0].name == "no_config_problem"
        # Should use default verifier
        assert result[0].config.verifier == "AnswerVerifier"
        # Should use default memory limit
        assert result[0].config.limits.memory == 512
