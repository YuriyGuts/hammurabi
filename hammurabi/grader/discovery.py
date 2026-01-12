"""
Discovers problems, solutions, and test cases from the filesystem.

Expected directory layout:

    problems/
    |-- problem1_name/
    |   |-- solutions/
    |   |   |-- author1_name/
    |   |   |   |-- sourcefile1.java
    |   |   |   |-- sourcefile2.java
    |   |   |-- author2_name/
    |   |   |   |-- sourcefile1.py
    |   |-- testcases/
    |   |   |-- 01.in
    |   |   |-- 02.in
    |   |-- answers/
    |   |   |-- 01.out
    |   |   |-- 02.out
    |   |-- problem.yaml
    |-- problem2_name/
    |   |-- ...
"""

from __future__ import annotations

import itertools
from pathlib import Path

from hammurabi.grader import adapters
from hammurabi.grader.config import GraderConfig
from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.utils import confreader


def _build_extension_to_language_map() -> dict[str, list[str]]:
    """Build a mapping from file extensions to languages that use them."""
    all_extensions = itertools.chain.from_iterable(
        adapter(None).get_preferred_extensions() or []
        for adapter in adapters.registered_adapters.values()
    )
    return {
        ext: [
            language
            for language, adapter in adapters.registered_adapters.items()
            if ext in (adapter(None).get_preferred_extensions() or [])
        ]
        for ext in all_extensions
    }


extension_to_language_map: dict[str, list[str]] = _build_extension_to_language_map()


def discover_problems(grader_config: GraderConfig) -> list[Problem]:
    """Discover all problems in the problem root directory."""
    result: list[Problem] = []
    problem_root = Path(grader_config.problem_root_dir)

    if not problem_root.exists():
        raise FileNotFoundError(
            f"Problems directory not found: {problem_root}\n\n"
            f"To fix this, either:\n"
            f"  1. Create the directory and add your problems there, or\n"
            f"  2. Update 'problem_root' in hammurabi.yaml to point to your problems directory."
        )

    for problem_path in _get_immediate_subdirs(problem_root):
        problem = Problem(problem_path.name, str(problem_path))

        # Read problem-specific config and merge with grader config
        problem_config = _read_problem_config(problem_path)
        problem.config = grader_config.merge_with(problem_config)

        # Set input/output filenames from config or defaults
        problem.input_filename = problem.config.problem_input_file or f"{problem.name}.in"
        problem.output_filename = problem.config.problem_output_file or f"{problem.name}.out"

        problem.testcases = _discover_testcases(problem)
        problem.solutions = _discover_solutions(problem)

        # Extract reference solution if present
        for index, solution in enumerate(problem.solutions):
            if solution.author == "_reference":
                problem.reference_solution = problem.solutions.pop(index)
                break

        result.append(problem)

    return result


def _read_problem_config(problem_path: Path) -> ProblemConfig:
    """Read the problem-specific configuration file."""
    config_path = problem_path / "problem.yaml"
    if not config_path.exists():
        return ProblemConfig()
    return confreader.read_problem_config(config_path)


def _discover_testcases(problem: Problem) -> list[TestCase]:
    """Discover all test cases for a problem."""
    problem_path = Path(problem.root_dir)
    testcase_dir = problem_path / "testcases"
    answers_dir = problem_path / "answers"

    result: list[TestCase] = []
    for input_path in sorted(testcase_dir.glob("*.in")):
        testcase_name = input_path.stem
        correct_answer_path = answers_dir / f"{testcase_name}.out"
        score = problem.config.get_testcase_score(testcase_name, default=1)

        testcase = TestCase(
            problem=problem,
            name=testcase_name,
            input_filename=str(input_path),
            correct_answer_filename=str(correct_answer_path),
            score=score,
        )
        result.append(testcase)

    return result


def _discover_solutions(problem: Problem) -> list[Solution]:
    """Discover all solutions for a problem."""
    solutions_root = Path(problem.root_dir) / "solutions"

    result: list[Solution] = []
    for solution_path in _get_immediate_subdirs(solutions_root):
        solution = Solution(
            problem=problem,
            author=solution_path.name,
            root_dir=str(solution_path),
        )

        # Find all source files recursively, excluding symlinks that escape the solution directory
        solution_path_resolved = solution_path.resolve()
        solution.files = sorted(
            str(f)
            for f in solution_path.rglob("*")
            if f.is_file()
            and f.suffix in extension_to_language_map
            and f.resolve().is_relative_to(solution_path_resolved)
        )

        solution.language = _detect_solution_language(solution)
        result.append(solution)

    return result


def _detect_solution_language(solution: Solution) -> str | None:
    """Detect the programming language of a solution based on file extensions."""
    if solution.root_dir is None:
        return None

    root_path = Path(solution.root_dir)
    root_path_resolved = root_path.resolve()
    language_counts: dict[str, int] = {}
    for file_path in root_path.rglob("*"):
        # Skip symlinks that escape the solution directory.
        if not file_path.resolve().is_relative_to(root_path_resolved):
            continue
        if file_path.suffix in extension_to_language_map:
            for language in extension_to_language_map[file_path.suffix]:
                language_counts[language] = language_counts.get(language, 0) + 1

    if not language_counts:
        return None

    return max(language_counts, key=lambda k: language_counts[k])


def _get_immediate_subdirs(root: Path) -> list[Path]:
    """Return a sorted list of immediate subdirectories."""
    return sorted(d for d in root.iterdir() if d.is_dir())
