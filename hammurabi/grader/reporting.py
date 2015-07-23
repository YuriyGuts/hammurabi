import csv
import datetime
import html
import os
import hammurabi.utils.fileio as fileio

from hammurabi.grader.model import *


report_metadata = {
    "testrun-log-csv": ["testruns.csv", "Execution Log [CSV]"],
    "matrix-csv": ["matrix.csv", "Matrix Report [CSV]"],
    "matrix-html": ["report-matrix.html", "Matrix Report [HTML]"],
    "full-html": ["report-full.html", "Execution Log [HTML]"],
}


def generate_testrun_log_csv(testruns, output_dir):
    report_filename = os.path.join(output_dir, report_metadata["testrun-log-csv"][0])
    testruns = sorted(testruns, key=lambda tr: tr.judge_start_time)

    with open(report_filename, "w") as csv_file:
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
                "details": _csv_escape_string(str(testrun.result.format_details()))[:1000],
            })

    return report_filename


def generate_matrix_report_csv(testruns, output_dir):
    report_filename = os.path.join(output_dir, report_metadata["matrix-csv"][0])
    headers, rows, scores, grand_totals = _get_matrix_report_data(testruns)

    with open(report_filename, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()

        for row in rows:
            row["problem"] = row["problem"].name
            row["testcase"] = row["testcase"].name

            for key in row:
                if isinstance(row[key], TestRunResult):
                    row[key] = row[key].status_code

            writer.writerow(row)

    return report_filename


def generate_matrix_report_html(testruns, output_dir):

    def begin_table(headers, header_cell_class):
        table_element = container.table(klass="table table-bordered text-center", style="width: auto;")
        table_header = table_element.thead(newlines=True)

        for header in headers:
            widths = {
                "problem": "150px",
                "testcase": "100px"
            }

            width = widths[header] if header in widths else "125px"
            table_header.th(header,
                klass="text-center {header_cell_class}".format(**locals()),
                style="width: {width};".format(**locals())
            )

        table_body_element = table_element.tbody(newlines=True)
        return table_body_element

    def generate_summary_row(table_body_element, summary_data_row, cell_class):
        subtotal_row = table_body_element.tr
        for header in headers:
            if header in non_author_headers:
                subtotal_row.td(klass="{cell_class}".format(**locals()))
            else:
                total_score = summary_data_row[header]["total_score"]
                maximum_score = summary_data_row[header]["maximum_score"]
                ratio = summary_data_row[header]["ratio"]
                subtotal = "{total_score} / {maximum_score} ({ratio:.0f}%)".format(**locals())
                subtotal_row.td(klass="{cell_class}".format(**locals())).strong(subtotal)

    report_filename = os.path.join(output_dir, report_metadata["matrix-html"][0])
    headers, data_rows, scores, grand_totals = _get_matrix_report_data(testruns)
    non_author_headers = ["problem", "testcase"]
    full_report_link = report_metadata["full-html"][0]

    doc = html.HTML("html")
    report_title = "Progress Matrix Report"

    head = doc.head()
    head.title(report_title)
    css = fileio.read_entire_file(os.path.join(os.path.dirname(__file__), "resources", "report.css"))
    style = head.style(type="text/css").raw_text(css)

    body = doc.body(newlines=True)
    container = body.div(klass="container")
    _create_html_report_cross_reference_section(container)

    report_header = container.div(klass="page-header")
    report_header.h1(report_title)
    now = datetime.datetime.now()
    container.p("Last updated: {now:%Y-%m-%d %H:%M}".format(**locals()))

    container.h3("Legend")
    legend_table = container.table(klass="table table-bordered", style="width: auto;")
    results = [
        TestRunCorrectAnswerResult(),
        TestRunWrongAnswerResult(),
        TestRunTimeoutResult(),
        TestRunRuntimeErrorResult(message=None),
        TestRunFormatErrorResult(message=None),
        TestRunCompilationErrorResult(message=None),
        TestRunSolutionMissingResult(),
        TestRunInternalErrorResult(exception=None),
    ]
    for result in results:
        legend_row = legend_table.tr
        style = _get_contextual_style_by_result(result)
        legend_row.td(
            "{result.status_code}".format(**locals()),
            klass="bg-{style} text-center".format(**locals()),
            style="width: 50px;"
        )
        legend_row.td(
            "{result.status}".format(**locals()),
            klass="bg-{style}".format(**locals())
        )

    previous_problem = None
    table_body = None

    for (data_row_index, data_row) in enumerate(data_rows):
        problem = data_row["problem"]
        testcase = data_row["testcase"]

        if problem != previous_problem:
            problem_header = container.div(klass="page-header")
            problem_header.h2("Problem: {problem.name}".format(**locals()))

            previous_problem = problem
            table_body = begin_table(headers, "bg-primary")

        table_row = table_body.tr()
        table_row.td(problem.name)
        table_row.td(testcase.name)

        for header in headers:
            author = header
            if isinstance(data_row[author], TestRunResult):
                result = data_row[author]
                background = _get_contextual_style_by_result(result)
                cell = table_row.td(klass="bg-{background} result-link-cell".format(**locals()))

                testcase_log_link = "{full_report_link}#{problem.name}-{author}-{testcase.name}".format(**locals())
                result_details = result.format_details()
                result_details = "" if result_details is None else str(result.format_details())[:1000]
                tooltip = "{result.status}\n\n{result_details}".format(**locals())

                cell.a(result.status_code, href=testcase_log_link, title=tooltip)

        if data_row_index == len(data_rows) - 1 or data_rows[data_row_index + 1]["problem"] != data_rows[data_row_index]["problem"]:
            generate_summary_row(table_body, scores[problem.name], "bg-primary")

    grand_total_header = container.div(klass="page-header")
    grand_total_header.h1("Grand Total")

    grand_total_table_body = begin_table(headers, "bg-primary")
    generate_summary_row(grand_total_table_body, grand_totals, "bg-info")

    html_content = str(doc)
    fileio.write_entire_file(report_filename, html_content)
    return report_filename


def generate_full_log_html(testruns, output_dir):

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

    report_filename = os.path.join(output_dir, report_metadata["full-html"][0])
    testruns = sorted(testruns, key=lambda tr: (tr.testcase.problem.name, tr.solution.author, tr.judge_start_time))

    doc = html.HTML("html")
    report_title = "Solution Execution Log"

    head = doc.head()
    head.title(report_title)
    css = fileio.read_entire_file(os.path.join(os.path.dirname(__file__), "resources", "report.css"))
    style = head.style(type="text/css").raw_text(css)

    body = doc.body(newlines=True)
    container = body.div(klass="container")
    _create_html_report_cross_reference_section(container)

    report_header = container.div(klass="page-header")
    report_header.h1(report_title)
    now = datetime.datetime.now()
    container.p("Last updated: {now:%Y-%m-%d %H:%M}".format(**locals()))

    previous_problem = None
    previous_author = None

    for testrun in testruns:
        if testrun.testcase.problem.name != previous_problem:
            previous_problem = testrun.testcase.problem.name
            problem_header = container.div(klass="page-header")
            problem_header.h2("Problem: {testrun.testcase.problem.name}".format(**locals()))

        if testrun.solution.author != previous_author:
            previous_author = testrun.solution.author
            solution_header = container.h3("Solution: {testrun.solution.author}".format(**locals()))
            solution_header.small(" (Problem: {testrun.testcase.problem.name}, Language: {testrun.solution.language})".format(**locals()))

        result_style = _get_contextual_style_by_result(testrun.result)
        testcase_header_text = "Testcase: {testrun.testcase.name}".format(**locals())
        anchor_name = "{testrun.testcase.problem.name}-{testrun.solution.author}-{testrun.testcase.name}".format(**locals())
        container.a("", name=anchor_name)

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
    fileio.write_entire_file(report_filename, html_content)
    return report_filename


def _get_matrix_report_data(testruns):
    rows = []
    scores = {}
    max_score_per_problem = {}
    grand_totals = {}

    headers = ["problem", "testcase"]
    unique_authors = sorted(list(set([testrun.solution.author for testrun in testruns])))
    unique_problems = sorted(list(set([testrun.solution.problem.name for testrun in testruns])))
    headers.extend(unique_authors)

    for problem_name in unique_problems:
        scores[problem_name] = {}
        max_score_per_problem[problem_name] = 0

        for author_name in unique_authors:
            scores[problem_name][author_name] = {}
            scores[problem_name][author_name]["total_score"] = 0
            grand_totals[author_name] = {}
            grand_totals[author_name]["total_score"] = 0
            grand_totals[author_name]["maximum_score"] = 0

    for problem_name in unique_problems:
        unique_testcases = sorted(list(set([
            testrun.testcase.name
            for testrun in testruns
            if testrun.solution.problem.name == problem_name
        ])))

        for testcase_name in unique_testcases:
            row = {
                "problem": [
                    testrun.solution.problem
                    for testrun in testruns
                    if testrun.solution.problem.name == problem_name
                ][0],
                "testcase": [
                    testrun.testcase
                    for testrun in testruns
                    if testrun.testcase.name == testcase_name and testrun.solution.problem.name == problem_name
                ][0],
            }

            max_score_per_problem[row["problem"].name] += row["testcase"].score

            for author_name in unique_authors:
                testrun = [
                    testrun
                    for testrun in testruns
                    if testrun.solution.author == author_name and testrun.testcase.name == testcase_name and testrun.solution.problem.name == problem_name
                ]

                if len(testrun) > 0:
                    row[author_name] = testrun[0].result
                    scores[problem_name][author_name]["total_score"] += testrun[0].result.score
                else:
                    missing_result = TestRunSolutionMissingResult()
                    missing_result.score = 0
                    row[author_name] = missing_result

            rows.append(row)

    for problem_name in scores:
        for author_name in scores[problem_name]:
            score_dict = scores[problem_name][author_name]
            score_dict["maximum_score"] = max_score_per_problem[problem_name]
            score_dict["ratio"] = score_dict["total_score"] * 100.0 / score_dict["maximum_score"]

            grand_totals[author_name]["total_score"] += score_dict["total_score"]
            grand_totals[author_name]["maximum_score"] += score_dict["maximum_score"]

    for author_name in grand_totals:
        grand_totals[author_name]["ratio"] = grand_totals[author_name]["total_score"] * 100.0 / grand_totals[author_name]["maximum_score"]

    return headers, rows, scores, grand_totals


def _create_html_report_cross_reference_section(element):
    link_row = element.div(klass="row cross-reference-row")
    for report_codename in ["matrix-html", "full-html", "matrix-csv", "testrun-log-csv"]:
        filename, report_name = report_metadata[report_codename]
        cell = link_row.div(klass="col-md-3")
        cell.a(report_name, href=filename)


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
        TestRunSolutionMissingResult: "warning",
        TestRunTimeoutResult: "info",
        TestRunUnverifiedResult: "primary",
        TestRunWrongAnswerResult: "danger",
    }
    result_type = type(testrun_result)
    return "default" if result_type not in contextual_style_by_result else contextual_style_by_result[result_type]


def _csv_escape_string(string):
    return ''.join([i if 32 < ord(i) < 128 else ' ' for i in string])
