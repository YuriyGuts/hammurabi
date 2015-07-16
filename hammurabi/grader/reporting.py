import csv
import datetime
import html
import os
import subprocess
import hammurabi.utils.fileio as fileio

from hammurabi.grader.model import *


def generate_testrun_log_csv(testruns, output_filename):
    testruns = sorted(testruns, key=lambda tr: tr.judge_start_time)

    with open(output_filename, "w") as csv_file:
        field_names = ["start_time", "end_time", "problem_name", "solution_author", "solution_language",
                       "testcase_name", "testcase_score", "result_status", "result_description", "score",
                       "solution_time", "overall_time"]

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
                "overall_time": testrun.get_judge_elapsed_milliseconds()
            })


def generate_full_log_html(testruns, output_filename):
    def create_testcase_summary_row(element, category, value):
        row = element.tr
        row.td(category)
        row.td().samp(value)

    def dump_file(element, header, filename):
        content = ""
        if os.path.exists(filename):
            content = fileio.read_entire_file(filename)
        dump_preformatted_text(element, header, content)

    def dump_preformatted_text(element, header, content):
        if content is not None and len(content.strip()) > 0:
            element.p(header)
            element.pre(content)
        else:
            element.p(header).em(" none.")

    testruns = sorted(testruns, key=lambda tr: (tr.testcase.problem.name, tr.solution.author, tr.judge_start_time))

    doc = html.HTML("html")

    head = doc.head()
    css = fileio.read_entire_file(os.path.join(os.path.dirname(__file__), "resources", "report.css"))
    style = head.style(type="text/css").raw_text(css)

    body = doc.body(newlines=True)
    container = body.div(klass="container")

    previous_problem = None
    previous_author = None

    for testrun in testruns:
        if testrun.testcase.problem.name != previous_problem:
            previous_problem = testrun.testcase.problem.name
            problem_header = container.div(klass="page-header")
            problem_header.h1("Problem: {testrun.testcase.problem.name}".format(**locals()))

        if testrun.solution.author != previous_author:
            previous_author = testrun.solution.author
            solution_header = container.h2("Solution: {testrun.solution.author}".format(**locals()))
            solution_header.small(" (Problem: {testrun.testcase.problem.name}, Language: {testrun.solution.language})".format(**locals()))

        result_style = _get_contextual_style_by_result(testrun.result)
        testcase_header_text = "Testcase: {testrun.testcase.name}".format(**locals())
        testcase_panel = container.div(klass="panel panel-{result_style}".format(**locals()))
        testcase_panel_header = testcase_panel.div(klass="panel-heading").h3(testcase_header_text, klass="panel-title")
        testcase_panel_content = testcase_panel.div(klass="panel-body")

        table = testcase_panel_content.table(newlines=True, klass="table table-bordered", style="width: auto;")

        judge_start_time = _get_readable_datetime(testrun.judge_start_time)
        judge_end_time = _get_readable_datetime(testrun.judge_end_time)
        solution_ms = testrun.get_lean_elapsed_milliseconds()
        overall_ms = testrun.get_judge_elapsed_milliseconds()
        judge_overhead_ms = overall_ms - solution_ms

        create_testcase_summary_row(table, "Judging Date", "{judge_start_time} -- {judge_end_time}".format(**locals()))
        create_testcase_summary_row(table, "Solution Time", "{solution_ms} ms".format(**locals()))
        create_testcase_summary_row(table, "Overall Time", "{overall_ms} ms (judge overhead: {judge_overhead_ms} ms)".format(**locals()))
        create_testcase_summary_row(table, "Result", "[{testrun.result.status_code}] {testrun.result.status}".format(**locals()))
        create_testcase_summary_row(table, "Score", "{testrun.result.score}".format(**locals()))

        dump_preformatted_text(testcase_panel_content, "Result details:", testrun.result.format_details())
        dump_file(testcase_panel_content, "Compiler output:", testrun.compiler_output_filename)
        dump_file(testcase_panel_content, "Standard output stream:", testrun.stdout_filename)
        dump_file(testcase_panel_content, "Standard error stream:", testrun.stderr_filename)

    html_content = str(doc)
    fileio.write_entire_file(output_filename, html_content)


def _get_readable_datetime(ms_timestamp):
    dt = datetime.datetime.fromtimestamp(ms_timestamp / 1000.0)
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')


def _get_contextual_style_by_result(testrun_result):
    contextual_style_by_result = {
        TestRunCompilationErrorResult: "warning",
        TestRunCorrectAnswerResult: "success",
        TestRunFormatErrorResult: "warning",
        TestRunInternalErrorResult: "warning",
        TestRunRuntimeErrorResult: "warning",
        TestRunSolutionMissingResult: "default",
        TestRunTimeoutResult: "info",
        TestRunUnverifiedResult: "primary",
        TestRunWrongAnswerResult: "danger",
    }
    result_type = type(testrun_result)
    return "default" if result_type not in contextual_style_by_result else contextual_style_by_result[result_type]
