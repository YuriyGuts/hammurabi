"""
Discovers problems, solutions, and test cases from the filesystem.

Expected directory layout:

|
|-- %problem1_name%
|   |-- solutions
|   |   |-- %author1_name%
|   |   |   |-- %sourcefile1%.java
|   |   |   |-- %sourcefile2%.java
|   |   |-- %author2_name%
|   |   |   |-- %sourcefile1%.py
|   |   |-- %author3_name%
|   |   |   |-- (...arbitrary tree depth...)
|   |   |   | ...... |-- %sourcefile%.java
|   |-- testcases
|   |   |-- 01.in
|   |   |-- 02.in
|   |   |-- 03.in
|   |-- answers
|   |   |-- 01.out
|   |   |-- 02.out
|   |   |-- 03.out
|   |-- problem.conf
|-- %problem2_name%
|   |-- solutions
|   |-- testcases
|   |-- answers
|   |-- problem.conf
"""

from __future__ import annotations

import glob
import itertools
import os

from hammurabi.grader import adapters
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.utils import confreader
from hammurabi.utils.config import GraderConfig
from hammurabi.utils.config import ProblemConfig

# Reshape {language: [ext, ext, ...]} to {ext: [language, language, ...]}.
extension_to_language_map: dict[str, list[str]] = {
    ext: [
        language
        for language, adapter in adapters.registered_adapters.items()
        if ext in (adapter(None).get_preferred_extensions() or [])
    ]
    for ext in list(
        itertools.chain.from_iterable(
            [
                adapter(None).get_preferred_extensions() or []
                for _language, adapter in adapters.registered_adapters.items()
            ]
        )
    )
}


def discover_problems(grader_config: GraderConfig) -> list[Problem]:
    """Discover all problems in the problem root directory."""
    result: list[Problem] = []

    for problem_dir in get_immediate_subdirs(grader_config.problem_root_dir):
        problem_name = os.path.basename(problem_dir)

        problem = Problem(problem_name, problem_dir)

        # Read problem-specific config and merge with grader config
        problem_config = read_problem_config(problem)
        problem.config = grader_config.merge_with(problem_config)

        # Set input/output filenames from config or defaults
        problem.input_filename = (
            problem.config.problem_input_file
            if problem.config.problem_input_file
            else problem.name + ".in"
        )
        problem.output_filename = (
            problem.config.problem_output_file
            if problem.config.problem_output_file
            else problem.name + ".out"
        )

        problem.testcases = discover_testcases(problem)
        problem.solutions = discover_solutions(problem)

        reference_solution_index = None
        for index, solution in enumerate(problem.solutions):
            if solution.author == "_reference":
                reference_solution_index = index
                problem.reference_solution = solution

        if reference_solution_index is not None:
            problem.solutions.pop(reference_solution_index)

        result.append(problem)

    return result


def read_problem_config(problem: Problem) -> ProblemConfig:
    """Read the problem-specific configuration file."""
    config_filename = os.path.join(problem.root_dir, "problem.conf")
    return confreader.read_problem_config(config_filename)


def discover_testcases(problem: Problem) -> list[TestCase]:
    """Discover all test cases for a problem."""
    result: list[TestCase] = []
    testcase_dir = os.path.join(problem.root_dir, "testcases")

    for input_filename in get_files_by_glob_pattern(testcase_dir, "*.in"):
        testcase_name, _ = os.path.splitext(os.path.basename(input_filename))
        correct_answer_filename = os.path.join(problem.root_dir, "answers", testcase_name + ".out")
        score = problem.config.get_testcase_score(testcase_name, default=1)

        testcase = TestCase(
            problem=problem,
            name=testcase_name,
            input_filename=input_filename,
            correct_answer_filename=correct_answer_filename,
            score=score,
        )
        result.append(testcase)

    return result


def discover_solutions(problem: Problem) -> list[Solution]:
    """Discover all solutions for a problem."""
    result: list[Solution] = []
    solutions_root_dir = os.path.join(problem.root_dir, "solutions")

    for solution_dir in get_immediate_subdirs(solutions_root_dir):
        author = os.path.basename(solution_dir)
        solution = Solution(problem=problem, author=author, root_dir=solution_dir)

        solution.files = []
        for root, _dirs, files in os.walk(solution_dir):
            solution.files.extend(
                [
                    os.path.join(root, code_file)
                    for code_file in files
                    if os.path.splitext(code_file)[1] in extension_to_language_map
                ]
            )
        solution.files = sorted(solution.files)

        solution.language = detect_solution_language(solution)
        result.append(solution)

    return result


def detect_solution_language(solution: Solution) -> str | None:
    """Detect the programming language of a solution based on file extensions."""
    language_stats: dict[str, int] = {}

    # Counting the evidence of each language in the solution folder.
    for _root, _dirs, files in os.walk(solution.root_dir):
        for file in files:
            _filename, extension = [str(component) for component in os.path.splitext(file)]
            if extension in extension_to_language_map:
                for language in extension_to_language_map[extension]:
                    if language not in language_stats:
                        language_stats[language] = 0
                    language_stats[language] += 1

    if len(language_stats) == 0:
        return None

    return max(language_stats, key=lambda k: language_stats[k])


def get_immediate_subdirs(root_dir: str) -> list[str]:
    """Return a sorted list of immediate subdirectories."""
    return sorted(
        [
            os.path.join(root_dir, subdir)
            for subdir in os.listdir(root_dir)
            if os.path.isdir(os.path.join(root_dir, subdir))
        ]
    )


def get_files_by_glob_pattern(root_dir: str, pattern: str) -> list[str]:
    """Return files matching a glob pattern, sorted."""
    return sorted(glob.glob(os.path.join(root_dir, pattern)))
