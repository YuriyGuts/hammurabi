"""
Builds the object model for the grader assuming the following directory layout:

|
|-- %problem1_name%
    |-- solutions
        |-- %author1_name%
            |-- %sourcefile1%.java
            |-- %sourcefile2%.java
        |-- %author2_name%
            |-- %sourcefile1%.py
    |-- testcases
        |-- 01.in
        |-- 02.in
        |-- 03.in
    |-- answers
        |-- 01.out
        |-- 02.out
        |-- 03.out
    |-- problem.conf
|-- %problem2_name%
    |-- solutions
    |-- testcases
    |-- answers
    |-- problem.conf

"""

import glob
import os
import hammurabi.utils.confreader as confreader
from hammurabi.grader.model import *


extensions_to_exclude = {"", ".sh", ".in", ".out"}


def discover_problems(root_dir):
    result = []

    for problem_dir in get_immediate_subdirs(root_dir):
        problem_name = os.path.basename(problem_dir)

        problem = Problem(problem_name, problem_dir)
        problem.config = read_problem_config(problem)
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


def read_problem_config(problem):
    config_filename = os.path.join(problem.root_dir, "problem.conf")
    return confreader.read_config(config_filename)


def discover_testcases(problem):
    result = []
    testcase_dir = os.path.join(problem.root_dir, "testcases")

    for input_filename in get_files_by_glob_pattern(testcase_dir, "*.in"):
        testcase_basename = os.path.basename(input_filename)
        correct_answer_filename = os.path.join(problem.root_dir, "answers", testcase_basename.replace(".in", ".out"))
        score = problem.config.get_safe("testcase_score/{testcase_basename}".format(**locals()), default_value=1)

        testcase = TestCase(problem=problem,
                            name=testcase_basename,
                            input_filename=input_filename,
                            correct_answer_filename=correct_answer_filename,
                            score=score)
        result.append(testcase)

    return result


def discover_solutions(problem):
    result = []
    solutions_root_dir = os.path.join(problem.root_dir, "solutions")

    for solution_dir in get_immediate_subdirs(solutions_root_dir):
        author = os.path.basename(solution_dir)
        solution = Solution(problem=problem, author=author, root_dir=solution_dir)

        solution.files = []
        for root, dirs, files in os.walk(solution_dir):
            solution.files.extend([os.path.join(root, file)
                                   for file in files
                                   if os.path.splitext(file)[1] not in extensions_to_exclude])
        solution.files = sorted(solution.files)

        solution.language = detect_solution_language(solution)
        result.append(solution)

    return result


def detect_solution_language(solution):
    language_stats = {}

    extension_to_language_map = {
        ".c": "cpp",
        ".cpp": "cpp",
        ".cs": "csharp",
        ".java": "java",
        ".js": "javascript",
        ".php": "php",
        ".py": "python",
        ".rb": "ruby",
        ".scala": "scala",
    }

    for root, dirs, files in os.walk(solution.root_dir):
        for file in files:
            filename, extension = [str(component) for component in os.path.splitext(file)]
            if extension not in extensions_to_exclude and extension in extension_to_language_map:
                language = extension_to_language_map[extension]
                if language not in language_stats:
                    language_stats[language] = 0
                language_stats[language] += 1

    if len(language_stats) == 0:
        return None

    return max(language_stats, key=language_stats.get)


def get_immediate_subdirs(root_dir):
    return sorted([os.path.join(root_dir, subdir)
                   for subdir in os.listdir(root_dir)
                   if os.path.isdir(os.path.join(root_dir, subdir))])

def get_files_by_glob_pattern(root_dir, pattern):
    return sorted([filename for filename in glob.glob(os.path.join(root_dir, pattern))])
