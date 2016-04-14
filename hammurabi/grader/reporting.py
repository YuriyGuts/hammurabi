import colorsys
import csv
import datetime
import os
import time
import pickle
import hammurabi.utils.fileio as fileio

from hammurabi.grader.model import *
from jinja2 import FileSystemLoader
from jinja2.environment import Environment


def pickle_testruns(testruns, filename):
    with open(filename, "wb") as pickle_file:
        pickle.dump(testruns, pickle_file)


def generate_testrun_log_csv(testruns, filename):
    testruns = sorted(testruns, key=lambda tr: tr.judge_start_time)

    with open(filename, "w") as csv_file:
        field_names = ["start_time", "end_time", "problem_name", "solution_author", "solution_language",
                       "testcase_name", "testcase_score", "result_status", "result_description", "score",
                       "solution_time", "overall_time", "details"]

        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for testrun in testruns:
            writer.writerow({
                "start_time": testrun.judge_start_time,
                "end_time": testrun.judge_end_time,
                "problem_name": testrun.testcase.problem.name,
                "solution_author": testrun.solution.author,
                "solution_language": testrun.solution.language,
                "testcase_name": testrun.testcase.name,
                "testcase_score": testrun.testcase.score,
                "result_status": testrun.result.status_code,
                "result_description": testrun.result.status,
                "score": testrun.result.score,
                "solution_time": testrun.get_lean_elapsed_milliseconds(),
                "overall_time": testrun.get_judge_elapsed_milliseconds(),
                "details": csv_escape_string(str(testrun.result.format_details()))[:1000],
            })


def generate_full_log_html(testruns, filename):
    env = get_jinja_environment()
    report_name = "Solution Execution Log"
    report_date = time.time()
    content = env.get_template("report-full.html").render(**locals())
    fileio.write_entire_file(filename, content)


def generate_matrix_report_html(testruns, filename):
    env = get_jinja_environment()
    report_name = "Progress Matrix Report"
    report_date = time.time()
    legend_results = [
        TestRunCorrectAnswerResult(),
        TestRunWrongAnswerResult(),
        TestRunTimeoutResult(timeout=0),
        TestRunRuntimeErrorResult(message=None),
        TestRunFormatErrorResult(message=None),
        TestRunCompilationErrorResult(message=None),
        TestRunSolutionMissingResult(),
        TestRunInternalErrorResult(exception_info=None),
    ]
    content = env.get_template("report-matrix.html").render(**locals())
    fileio.write_entire_file(filename, content)


def generate_heatmap_report_html(testruns, filename):
    env = get_jinja_environment()
    for testrun in testruns:
        testrun.__dict__["data"] = {}
        if is_correct_answer(testrun):
            testrun.data["heatmap_adjusted_time"] = adjust_time_for_language(testrun.get_lean_elapsed_milliseconds(), testrun.solution.language)
        else:
            testrun.data["heatmap_adjusted_time"] = None

    unique_authors = sorted(list({testrun.solution.author for testrun in testruns}))
    unique_problems = sorted(list({testrun.solution.problem.name for testrun in testruns}))

    for problem in unique_problems:
        correct_testruns_for_problem = [
            testrun
            for testrun in testruns
            if testrun.solution.problem.name == problem and is_correct_answer(testrun)
        ]
        times = sorted([
            testrun.data["heatmap_adjusted_time"]
            for testrun in correct_testruns_for_problem
        ])
        for testrun in correct_testruns_for_problem:
            testrun.data["heatmap_percentile"] = percentile(times, testrun.data["heatmap_adjusted_time"])
            testrun.data["heatmap_heat_color"] = heat_color_for_percentile(testrun.data["heatmap_percentile"])

    report_name = "Time Heatmap Report"
    report_date = time.time()

    content = env.get_template("report-heatmap.html").render(**locals())
    fileio.write_entire_file(filename, content)


def get_jinja_environment():
    env = Environment()
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources", "templates"))
    env.loader = FileSystemLoader(template_path)
    env.filters.update({
        'format_timestamp': format_timestamp,
        'format_timestamp_micro': format_timestamp_micro,
        'dump': dump_preformatted_text,
        'dump_file': dump_file,
        'contextual_style': get_contextual_style_by_result,
        'is_correct_answer': is_correct_answer,
        'summary_statistics': summary_statistics
    })
    return env


def csv_escape_string(string):
    return ''.join([i if 32 < ord(i) < 128 else ' ' for i in string])


def format_timestamp(timestamp, format='%Y-%m-%d %H:%M:%S'):
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime(format)


def format_timestamp_micro(timestamp):
    datestring = format_timestamp(timestamp / 1000.0, format='%Y-%m-%d %H:%M:%S.%f')
    if len(datestring) > 3 and datestring[-3:] == "000":
        return datestring[:-3]


def dump_preformatted_text(content):
    truncate_limit = 1024
    if content is not None and len(content.strip()) > 0:
        if len(content) > truncate_limit:
            content = content[:truncate_limit] + "[content too long, truncated]"
    return content


def dump_file(filename):
    content = None
    if filename is not None and os.path.exists(filename):
        content = fileio.read_entire_file(filename)
    return dump_preformatted_text(content)


def get_contextual_style_by_result(testrun_result):
    contextual_style_by_result = {
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


def is_correct_answer(testrun):
    return testrun.result.is_correct()


def adjust_time_for_language(time, language):
    bootstrap_allowances = {
        "c": 0.0,
        "cpp": 0.0,
        "csharp": 0,
        "java": 30,
        "javascript": 0,
        "php": 0,
        "python": 0,
        "ruby": 0,
        "scala": 100
    }
    runtime_slowness_factors = {
        "c": 1.0,
        "cpp": 1.0,
        "csharp": 1.75,
        "java": 2.0,
        "javascript": 5.0,
        "php": 4.5,
        "python": 5.0,
        "ruby": 5.0,
        "scala": 3.5
    }
    slowness_factor_threshold = 50
    result = (time - bootstrap_allowances[language]) * 1.0
    if time - bootstrap_allowances[language] > slowness_factor_threshold:
        result = slowness_factor_threshold + (time - slowness_factor_threshold) * 1.0 / runtime_slowness_factors[language]

    return result


def percentile(data, value):
    if len(data) <= 1:
        return 0.0

    nearest_value_index = min(range(len(data)), key=lambda i: abs(data[i] - value))
    return nearest_value_index * 1.0 / (len(data) - 1)


def summary_statistics(data):
    try:
        mean = sum(data) * 1.0 / len(data)
        variance = sum([(value - mean) ** 2 for value in data]) / len(data)
        stddev = variance ** 0.5
        return mean, stddev
    except:
        return None, None


def heat_color_for_percentile(percentile):
    (r, g, b) = colorsys.hsv_to_rgb(0.3 * (1.0 - percentile) + 0.048, 0.2, 0.95)
    return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
