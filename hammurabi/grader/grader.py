import datetime
import os
import socket
import sys
import traceback
import hammurabi.utils.confreader as confreader
import hammurabi.grader.discovery as discovery
import hammurabi.grader.reporting as reporting

from hammurabi.grader.adapters import *
from hammurabi.grader.model import *
from hammurabi.grader.verifiers import *
from hammurabi.utils.exceptions import *


def grade(args):
    config = read_config()
    apply_locations_to_config(config)
    problems = discovery.discover_problems(config)
    scope = get_scope(problems, args, config)

    testruns = []

    try:
        for problem in scope.tasks:
            print
            print "Judging problem: {problem.name}".format(**locals())
            print "=" * 75

            for solution in scope.tasks[problem]:
                print
                print "Judging solution: {problem.name}   Author: {solution.author}   Language: {solution.language}".format(**locals())
                print "-" * 75

                testcases = scope.tasks[problem][solution]
                solution_testruns = judge_solution(solution, testcases)
                testruns.extend(solution_testruns)

    except KeyboardInterrupt:
        pass

    produce_report(config, testruns)


def read_config():
    filename = os.path.join(os.path.dirname(__file__), "grader.conf")
    return confreader.read_config(filename)


def get_scope(problems, args, config):
    tasks = {}
    problems_to_run = [
        problem
        for problem in problems
        if args.problem is None or problem.name in args.problem
    ]

    for problem in problems_to_run:
        tasks[problem] = {}

        solutions_to_run = [
            solution
            for solution in problem.solutions
            if args.author is None or solution.author in args.author
        ] if not args.reference else [problem.reference_solution]

        testcases_to_run = [
            testcase
            for testcase in problem.testcases
            if args.testcase is None or testcase.name in args.testcase
        ]

        for solution in solutions_to_run:
            tasks[problem][solution] = []

            for testcase in testcases_to_run:
                tasks[problem][solution].append(testcase)

    return GraderJobScope(tasks)


def apply_locations_to_config(config):
    config.problem_root_dir = get_problem_root_dir(config)
    config.report_root_dir = get_report_root_dir(config)
    config.report_output_dir = get_report_output_dir(config)


def get_problem_root_dir(config):
    problem_root_dir = config.get_safe("locations/problem_root", default_value="problems")
    if not os.path.isabs(problem_root_dir):
        problem_root_dir = os.path.join(os.path.dirname(__file__), problem_root_dir)
    return problem_root_dir


def get_report_root_dir(config):
    report_root_dir = config.get_safe("locations/report_root", default_value="reports")
    if not os.path.isabs(report_root_dir):
        report_root_dir = os.path.join(os.path.dirname(__file__), report_root_dir)
    return report_root_dir


def get_report_output_dir(config):
    dt = datetime.datetime.now()
    hostname = socket.getfqdn()
    report_output_dir_name = str(config.get_safe("locations/report_folder_template")).format(**locals())
    report_output_dir = os.path.join(config.report_root_dir, report_output_dir_name)
    os.makedirs(report_output_dir)
    return report_output_dir


def judge_solution(solution, testcases):
    try:
        adapter = create_adapter(solution)
        adapter.prepare()
    except:
        print "An internal error has occurred while judging the solution."
        traceback.print_exc()

    testruns = []
    for testcase in testcases:
        try:
            print "Running test case: {testcase.name} (score: {testcase.score})".format(**locals()),
            try:
                testrun = adapter.create_testrun(testcase)
                testrun.record_judge_start_time()
                adapter.run(testrun)

                if solution != solution.problem.reference_solution:
                    verifier = create_verifier(testrun)
                    is_correct = verifier.verify(testrun)
                else:
                    testrun.result = TestRunUnverifiedResult("Verification ignored - running the reference solution.")

            except TestRunPrematureTerminationError as e:
                testrun.result = e.result

            if isinstance(testrun.result, TestRunCorrectAnswerResult):
                testrun.result.score = testrun.testcase.score
            else:
                testrun.result.score = 0

        except KeyboardInterrupt:
            raise

        except:
            e = sys.exc_info()
            testrun.result = TestRunInternalErrorResult(e)

        testrun.record_judge_end_time()
        lean_time_elapsed = testrun.get_lean_elapsed_milliseconds()
        judge_time_elapsed = testrun.get_judge_elapsed_milliseconds()
        judge_overhead = judge_time_elapsed - lean_time_elapsed

        print "-> {testrun.result}, Time: {lean_time_elapsed} ms, Overall time: {judge_time_elapsed} (+{judge_overhead}) ms".format(**locals())
        testruns.append(testrun)

    return testruns


def create_adapter(solution):
    if solution.language == "java":
        return JavaSolutionAdapter(solution)
    elif solution.language == "javascript":
        return JavaScriptSolutionAdapter(solution)
    elif solution.language == "csharp":
        return CSharpSolutionAdapter(solution)
    return BaseSolutionAdapter(solution)


def create_verifier(testrun):
    verifier_class = testrun.solution.problem.config.get_safe("verifier", default_value="AnswerVerifier")
    verifier = globals()[verifier_class]
    return verifier()


def produce_report(config, testruns):
    report_dir = config.report_output_dir

    testrun_csv_log_location = reporting.generate_testrun_log_csv(testruns, report_dir)
    matrix_csv_report_location = reporting.generate_matrix_report_csv(testruns, report_dir)
    matrix_html_report_location = reporting.generate_matrix_report_html(testruns, report_dir)
    full_html_log_location = reporting.generate_full_log_html(testruns, report_dir)

    print
    print "Reports:"
    print "CSV log:", testrun_csv_log_location
    print "Matrix CSV report:", matrix_csv_report_location
    print "Matrix HTML report:", matrix_html_report_location
    print "Detailed HTML log:", full_html_log_location
