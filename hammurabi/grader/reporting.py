"""Report generation for grading results."""

from __future__ import annotations

import colorsys
import csv
import datetime
import pickle
import time
from pathlib import Path

from jinja2 import FileSystemLoader
from jinja2.environment import Environment

from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunCompilationErrorResult
from hammurabi.grader.model import TestRunCorrectAnswerResult
from hammurabi.grader.model import TestRunFormatErrorResult
from hammurabi.grader.model import TestRunInternalErrorResult
from hammurabi.grader.model import TestRunResult
from hammurabi.grader.model import TestRunRuntimeErrorResult
from hammurabi.grader.model import TestRunSolutionMissingResult
from hammurabi.grader.model import TestRunTimeoutResult
from hammurabi.grader.model import TestRunUnverifiedResult
from hammurabi.grader.model import TestRunWrongAnswerResult
from hammurabi.utils import fileio

# Constants for CSV escaping
ASCII_SPACE_ORD = 32
ASCII_TILDE_ORD = 128
MICROSECOND_SUFFIX_LEN = 3


def pickle_testruns(testruns: list[TestRun], filename: str) -> None:
    """Serialize test runs to a pickle file."""
    with open(filename, "wb") as pickle_file:
        pickle.dump(testruns, pickle_file)


def generate_testrun_log_csv(testruns: list[TestRun], filename: str) -> None:
    """Generate a CSV log of all test runs."""
    testruns = sorted(testruns, key=lambda tr: tr.judge_start_time or 0)

    with open(filename, "w") as csv_file:
        field_names = [
            "start_time",
            "end_time",
            "problem_name",
            "solution_author",
            "solution_language",
            "testcase_name",
            "testcase_score",
            "result_status",
            "result_description",
            "score",
            "solution_time",
            "overall_time",
            "details",
        ]

        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for testrun in testruns:
            details = testrun.result.format_details() if testrun.result else ""
            writer.writerow(
                {
                    "start_time": testrun.judge_start_time,
                    "end_time": testrun.judge_end_time,
                    "problem_name": testrun.testcase.problem.name,
                    "solution_author": testrun.solution.author,
                    "solution_language": testrun.solution.language,
                    "testcase_name": testrun.testcase.name,
                    "testcase_score": testrun.testcase.score,
                    "result_status": testrun.result.status_code if testrun.result else "",
                    "result_description": testrun.result.status if testrun.result else "",
                    "score": testrun.result.score if testrun.result else 0,
                    "solution_time": testrun.get_lean_elapsed_milliseconds(),
                    "overall_time": testrun.get_judge_elapsed_milliseconds(),
                    "details": csv_escape_string(str(details))[:1000],
                }
            )


def generate_full_log_html(testruns: list[TestRun], filename: str) -> None:
    """Generate a detailed HTML log of all test runs."""
    env = get_jinja_environment()
    report_name = "Solution Execution Log"
    report_date = time.time()
    content = env.get_template("report-full.html").render(
        env=env,
        report_name=report_name,
        report_date=report_date,
        testruns=testruns,
        filename=filename,
    )
    fileio.write_entire_file(filename, content)


def generate_matrix_report_html(testruns: list[TestRun], filename: str) -> None:
    """Generate a matrix-style HTML report."""
    env = get_jinja_environment()
    report_name = "Progress Matrix Report"
    report_date = time.time()
    legend_results: list[TestRunResult] = [
        TestRunCorrectAnswerResult(),
        TestRunWrongAnswerResult(),
        TestRunTimeoutResult(timeout=0),
        TestRunRuntimeErrorResult(message=None),
        TestRunFormatErrorResult(message=""),
        TestRunCompilationErrorResult(message=None),
        TestRunSolutionMissingResult(),
        TestRunInternalErrorResult(exception_info=None),
    ]
    content = env.get_template("report-matrix.html").render(
        env=env,
        report_name=report_name,
        report_date=report_date,
        legend_results=legend_results,
        testruns=testruns,
        filename=filename,
    )
    fileio.write_entire_file(filename, content)


def generate_heatmap_report_html(testruns: list[TestRun], filename: str) -> None:
    """Generate a time-based heatmap HTML report."""
    env = get_jinja_environment()
    for testrun in testruns:
        testrun.__dict__["data"] = {}
        if is_correct_answer(testrun):
            testrun.data["heatmap_adjusted_time"] = adjust_time_for_language(
                testrun.get_lean_elapsed_milliseconds(), testrun.solution.language
            )
        else:
            testrun.data["heatmap_adjusted_time"] = None

    unique_authors = sorted({testrun.solution.author for testrun in testruns})
    unique_problems = sorted({testrun.solution.problem.name for testrun in testruns})

    for problem in unique_problems:
        correct_testruns_for_problem = [
            testrun
            for testrun in testruns
            if testrun.solution.problem.name == problem and is_correct_answer(testrun)
        ]
        times = sorted(
            [testrun.data["heatmap_adjusted_time"] for testrun in correct_testruns_for_problem]
        )
        for testrun in correct_testruns_for_problem:
            testrun.data["heatmap_percentile"] = percentile(
                times, testrun.data["heatmap_adjusted_time"]
            )
            testrun.data["heatmap_heat_color"] = heat_color_for_percentile(
                testrun.data["heatmap_percentile"]
            )

    report_name = "Time Heatmap Report"
    report_date = time.time()

    content = env.get_template("report-heatmap.html").render(
        env=env,
        report_name=report_name,
        report_date=report_date,
        unique_authors=unique_authors,
        unique_problems=unique_problems,
        testruns=testruns,
        filename=filename,
    )
    fileio.write_entire_file(filename, content)


def get_jinja_environment() -> Environment:
    """Create and configure the Jinja2 environment."""
    env = Environment()
    template_path = Path(__file__).parent / "resources" / "templates"
    env.loader = FileSystemLoader(template_path)
    env.filters.update(
        {
            "format_timestamp": format_timestamp,
            "format_timestamp_micro": format_timestamp_micro,
            "dump": dump_preformatted_text,
            "dump_file": dump_file,
            "contextual_style": get_contextual_style_by_result,
            "is_correct_answer": is_correct_answer,
            "summary_statistics": summary_statistics,
        }
    )
    return env


def csv_escape_string(string: str) -> str:
    """Escape non-printable characters for CSV output."""
    return "".join([i if ASCII_SPACE_ORD < ord(i) < ASCII_TILDE_ORD else " " for i in string])


def format_timestamp(timestamp: float, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a Unix timestamp as a date string."""
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime(format)


def format_timestamp_micro(timestamp: float) -> str | None:
    """Format a millisecond timestamp with microsecond precision."""
    datestring = format_timestamp(timestamp / 1000.0, format="%Y-%m-%d %H:%M:%S.%f")
    if len(datestring) > MICROSECOND_SUFFIX_LEN and datestring[-MICROSECOND_SUFFIX_LEN:] == "000":
        return datestring[:-MICROSECOND_SUFFIX_LEN]
    return None


def dump_preformatted_text(content: str | None) -> str | None:
    """Truncate content if it's too long for display."""
    truncate_limit = 1024
    if content is not None and len(content.strip()) > 0 and len(content) > truncate_limit:
        content = content[:truncate_limit] + "[content too long, truncated]"
    return content


def dump_file(filename: str | None) -> str | None:
    """Read and dump file contents, truncating if necessary."""
    if filename is None:
        return None
    path = Path(filename)
    if not path.exists():
        return None
    return dump_preformatted_text(fileio.read_entire_file(filename))


def get_contextual_style_by_result(testrun_result: TestRunResult) -> str:
    """Return the Bootstrap contextual style for a result type."""
    contextual_style_by_result: dict[type[TestRunResult], str] = {
        TestRunCompilationErrorResult: "warning",
        TestRunCorrectAnswerResult: "success",
        TestRunFormatErrorResult: "warning",
        TestRunInternalErrorResult: "warning",
        TestRunRuntimeErrorResult: "warning",
        TestRunSolutionMissingResult: "warning",
        TestRunTimeoutResult: "info",
        TestRunUnverifiedResult: "primary",
        TestRunWrongAnswerResult: "danger",
    }
    result_type = type(testrun_result)
    return contextual_style_by_result.get(result_type, "default")


def is_correct_answer(testrun: TestRun) -> bool:
    """Check if a test run has a correct answer."""
    return testrun.result is not None and testrun.result.is_correct()


def adjust_time_for_language(time: int, language: str | None) -> float:
    """Adjust execution time to account for language performance differences."""
    bootstrap_allowances: dict[str, float] = {
        "c": 0.0,
        "cpp": 0.0,
        "csharp": 0,
        "java": 30,
        "javascript": 0,
        "php": 0,
        "python": 0,
        "ruby": 0,
    }
    runtime_slowness_factors: dict[str, float] = {
        "c": 1.0,
        "cpp": 1.0,
        "csharp": 1.75,
        "java": 2.0,
        "javascript": 5.0,
        "php": 4.5,
        "python": 5.0,
        "ruby": 5.0,
    }

    slowness_factor_threshold = 50
    lang = language or ""
    result = (time - bootstrap_allowances.get(lang, 0.0)) * 1.0
    if time - bootstrap_allowances.get(lang, 0.0) > slowness_factor_threshold:
        result = slowness_factor_threshold + (
            time - slowness_factor_threshold
        ) * 1.0 / runtime_slowness_factors.get(lang, 1.0)

    return result


def percentile(data: list[float], value: float) -> float:
    """Calculate the percentile rank of a value in a sorted list."""
    if len(data) <= 1:
        return 0.0

    nearest_value_index = min(range(len(data)), key=lambda i: abs(data[i] - value))
    return nearest_value_index * 1.0 / (len(data) - 1)


def summary_statistics(data: list[float]) -> tuple[float | None, float | None]:
    """Calculate mean and standard deviation."""
    try:
        mean = sum(data) * 1.0 / len(data)
        variance = sum([(value - mean) ** 2 for value in data]) / len(data)
        stddev = variance**0.5
        return mean, stddev
    except Exception:
        return None, None


def heat_color_for_percentile(percentile: float) -> str:
    """Convert a percentile to a heat map color."""
    (r, g, b) = colorsys.hsv_to_rgb(0.3 * (1.0 - percentile) + 0.048, 0.2, 0.95)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
