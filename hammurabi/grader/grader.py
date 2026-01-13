"""Main grading logic."""

from __future__ import annotations

import argparse
import datetime
import shutil
import socket
import traceback
from pathlib import Path

from hammurabi.exceptions import TestRunPrematureTerminationError
from hammurabi.exceptions import VerifierCreationError
from hammurabi.grader import adapters
from hammurabi.grader import discovery
from hammurabi.grader import reporting
from hammurabi.grader import verifiers
from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.config import GraderConfig
from hammurabi.grader.model import GraderJobScope
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunInternalErrorResult
from hammurabi.grader.model import TestRunSolutionMissingResult
from hammurabi.grader.model import TestRunUnverifiedResult
from hammurabi.grader.verifiers.common import AnswerVerifier
from hammurabi.utils import confreader
from hammurabi.utils import terminal


def grade(args: argparse.Namespace) -> None:
    """Run the grading process."""
    config = _read_config(args)
    _apply_locations_to_config(config)
    _load_custom_verifiers()
    problems = discovery.discover_problems(config)
    scope = _get_scope(problems, args)

    testruns: list[TestRun] = []

    try:
        for problem in scope.tasks:
            print()
            print(terminal.cyan_bold(f"Judging problem: {problem.name}"))
            print(terminal.dim("=" * 75))

            for solution in scope.tasks[problem]:
                print()
                print(
                    terminal.cyan(
                        f"Judging solution: {problem.name}   "
                        f"Author: {solution.author}   "
                        f"Language: {solution.language}"
                    )
                )
                print(terminal.dim("-" * 75))

                testcases = scope.tasks[problem][solution]
                solution_testruns = judge_solution(solution, testcases)
                testruns.extend(solution_testruns)

    except KeyboardInterrupt:
        pass

    testruns = _fill_testruns_for_missing_solutions(testruns)
    _generate_reports(config, testruns)


def _read_config(args: argparse.Namespace) -> GraderConfig:
    """Read and return the grader configuration."""
    if args.conf is not None:
        config_file = Path(args.conf).resolve()
        if not config_file.exists():
            raise OSError(f"Configuration file '{config_file}' not found.")
        return confreader.read_grader_config(str(config_file))

    # Search for config in current working directory
    cwd = Path.cwd()
    config_file = cwd / "hammurabi.yaml"
    if not config_file.exists():
        raise OSError(
            f"Configuration file 'hammurabi.yaml' not found in {cwd}.\n"
            "Please create a hammurabi.yaml configuration file."
        )
    return confreader.read_grader_config(str(config_file))


def _get_scope(problems: list[Problem], args: argparse.Namespace) -> GraderJobScope:
    """Build the scope of problems, solutions, and test cases to grade."""
    tasks: dict[Problem, dict[Solution, list[TestCase]]] = {}
    problems_to_run = [
        problem for problem in problems if args.problem is None or problem.name in args.problem
    ]

    for problem in problems_to_run:
        tasks[problem] = {}

        solutions_to_run = (
            [
                solution
                for solution in problem.solutions
                if args.author is None or solution.author in args.author
            ]
            if not args.reference
            else [problem.reference_solution]
        )

        testcases_to_run = [
            testcase
            for testcase in problem.testcases
            if args.testcase is None or testcase.name in args.testcase
        ]

        for solution in solutions_to_run:
            if solution is None:
                continue
            tasks[problem][solution] = []

            for testcase in testcases_to_run:
                tasks[problem][solution].append(testcase)

    return GraderJobScope(tasks)


def _apply_locations_to_config(config: GraderConfig) -> None:
    """Set up directory paths in the configuration."""
    config.problem_root_dir = _get_problem_root_dir(config)
    config.report_root_dir = _get_report_root_dir(config)
    config.report_output_dir = _get_report_output_dir(config)


def _get_problem_root_dir(config: GraderConfig) -> str:
    """Get the root directory for problems."""
    problem_root_path = Path(config.locations.problem_root)
    if not problem_root_path.is_absolute():
        problem_root_path = (Path.cwd() / problem_root_path).resolve()
    return str(problem_root_path)


def _get_report_root_dir(config: GraderConfig) -> str:
    """Get the root directory for reports."""
    report_root_path = Path(config.locations.report_root)
    if not report_root_path.is_absolute():
        report_root_path = (Path.cwd() / report_root_path).resolve()
    return str(report_root_path)


def _get_report_output_dir(config: GraderConfig) -> str:
    """Create and return the output directory for this grading run."""
    dt = datetime.datetime.now()
    hostname = socket.gethostname()
    template = config.locations.report_folder_template
    report_output_dir_name = template.format(dt=dt, hostname=hostname)
    report_output_path = Path(config.report_root_dir) / report_output_dir_name
    if report_output_path.exists():
        shutil.rmtree(report_output_path, ignore_errors=True)
    report_output_path.mkdir(parents=True)
    return str(report_output_path)


def _load_custom_verifiers() -> None:
    """Load custom verifiers from the 'verifiers' directory."""
    verifiers_dir = Path(__file__).parent / "verifiers"
    verifiers.load_custom_verifiers(verifiers_dir)


def judge_solution(solution: Solution, testcases: list[TestCase]) -> list[TestRun]:
    """Judge all test cases for a solution."""
    try:
        adapter = _create_adapter(solution)
        adapter.prepare()
    except Exception:
        print("Cannot create solution adapter.")
        traceback.print_exc()
        return []

    testruns: list[TestRun] = []
    for testcase in testcases:
        testrun = None
        try:
            print(
                f"Running test case: {testcase.name} (score: {testcase.score})",
                end=" ",
            )
            testrun = judge_testcase(solution, testcase, adapter)
        except KeyboardInterrupt:
            raise

        testrun.record_judge_end_time()
        lean_time_elapsed = testrun.get_lean_elapsed_milliseconds()
        judge_time_elapsed = testrun.get_judge_elapsed_milliseconds()
        judge_overhead = judge_time_elapsed - lean_time_elapsed

        result_str = testrun.result.colored_str() if testrun.result else ""
        print(
            f"-> {result_str}, Time: {lean_time_elapsed} ms, "
            f"Overall time: {judge_time_elapsed} (+{judge_overhead}) ms"
        )
        if isinstance(testrun.result, TestRunInternalErrorResult):
            print(terminal.red(testrun.result.format_details() or ""))

        testruns.append(testrun)

    return testruns


def judge_testcase(solution: Solution, testcase: TestCase, adapter: BaseSolutionAdapter) -> TestRun:
    """Judge a single test case."""
    testrun = adapter.create_testrun(testcase)
    try:
        testrun.record_judge_start_time()
        adapter.run(testrun)

        if solution != solution.problem.reference_solution:
            verifier = _create_verifier(testrun)
            verifier.verify(testrun)
        else:
            testrun.result = TestRunUnverifiedResult(
                "Verification ignored - running the reference solution."
            )

    except TestRunPrematureTerminationError as e:
        testrun.result = e.result

    except KeyboardInterrupt:
        raise

    except Exception as exc:  # noqa: BLE001 - Intentionally catching all exceptions from solution
        del exc  # Unused, we use traceback.format_exc() instead
        testrun.result = TestRunInternalErrorResult(exception_info=traceback.format_exc())

    if testrun.result is not None and testrun.result.is_correct():
        testrun.result.score = testrun.testcase.score
    elif testrun.result is not None:
        testrun.result.score = 0

    return testrun


def _create_adapter(solution: Solution) -> BaseSolutionAdapter:
    """Create the appropriate adapter for a solution's language."""
    if solution.language is None:
        return adapters.BaseSolutionAdapter(solution)
    cls = adapters.registered_adapters.get(solution.language, adapters.BaseSolutionAdapter)
    return cls(solution)


def _create_verifier(testrun: TestRun) -> AnswerVerifier:
    """Create a verifier for the test run."""
    verifier_name = testrun.solution.problem.config.verifier
    verifier_class = verifiers.registered_verifiers.get(verifier_name)
    if verifier_class is None:
        raise VerifierCreationError(
            f"Unknown verifier '{verifier_name}'. "
            f"Available: {', '.join(verifiers.registered_verifiers.keys())}"
        )
    return verifier_class()


def _fill_testruns_for_missing_solutions(testruns: list[TestRun]) -> list[TestRun]:
    """Add placeholder test runs for authors who didn't submit solutions."""
    padded_testruns = testruns
    unique_authors = sorted({testrun.solution.author for testrun in testruns})
    unique_problem_names = sorted({testrun.solution.problem.name for testrun in testruns})

    for problem_name in unique_problem_names:
        for author in unique_authors:
            # If this author hasn't attempted this problem,
            # create fake testruns with 'Solution Missing' result.
            if not any(
                testrun.solution.author == author and testrun.solution.problem.name == problem_name
                for testrun in testruns
            ):
                problem = next(
                    testrun.solution.problem
                    for testrun in testruns
                    if testrun.solution.problem.name == problem_name
                )
                solution = Solution(problem, author, None)

                for testcase in problem.testcases:
                    fake_testrun = TestRun(
                        solution=solution,
                        testcase=testcase,
                        output_dir=None,
                        answer_filename=None,
                        compiler_output_filename=None,
                        stdout_filename=None,
                        stderr_filename=None,
                        result=TestRunSolutionMissingResult(),
                    )
                    fake_testrun.record_judge_start_time()
                    fake_testrun.record_lean_start_time()
                    fake_testrun.record_lean_end_time()
                    fake_testrun.record_judge_end_time()
                    padded_testruns.append(fake_testrun)

    return padded_testruns


def _generate_reports(config: GraderConfig, testruns: list[TestRun]) -> None:
    """Generate all report files."""
    report_output_path = Path(config.report_output_dir)

    def get_report_path(relative_name: str) -> str:
        return str((report_output_path / relative_name).resolve())

    # Prepare paths.
    pickle_location = get_report_path("testruns.pickle")
    testrun_csv_log_location = get_report_path("testruns.csv")
    full_html_log_location = get_report_path("report-full.html")
    matrix_html_report_location = get_report_path("report-matrix.html")
    heatmap_html_report_location = get_report_path("report-heatmap.html")

    # Generate report files.
    reporting.pickle_testruns(testruns, pickle_location)
    reporting.generate_testrun_log_csv(testruns, testrun_csv_log_location)
    reporting.generate_full_log_html(testruns, full_html_log_location)
    reporting.generate_matrix_report_html(testruns, matrix_html_report_location)
    reporting.generate_heatmap_report_html(testruns, heatmap_html_report_location)

    # Copy the stylesheets used by the reports.
    styles_dir = Path(__file__).parent / "resources" / "styles"
    for css in styles_dir.glob("*.css"):
        shutil.copy(css, report_output_path)

    print()
    print(terminal.bold("Reports:"))
    print(terminal.dim("--------"))
    print("Pickled test runs:", terminal.green(pickle_location))
    print("CSV log:", terminal.green(testrun_csv_log_location))
    print("Detailed HTML log:", terminal.green(full_html_log_location))
    print("Matrix HTML report:", terminal.green(matrix_html_report_location))
    print("Heatmap HTML report:", terminal.green(heatmap_html_report_location))
