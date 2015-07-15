import datetime
import os
import socket
import traceback
import hammurabi.utils.confreader as confreader
import hammurabi.grader.discovery as discovery

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

    for problem in scope.tasks:
        print "Judging problem: {problem.name}".format(**locals())
        print "=" * 75

        for solution in scope.tasks[problem]:
            print
            print "Judging solution: {problem.name}   Author: {solution.author}   Language: {solution.language}".format(**locals())
            print "-" * 75

            testcases = scope.tasks[problem][solution]
            solution_testruns = judge_solution(solution, testcases)
            testruns.extend(solution_testruns)

    produce_report(testruns)


def read_config():
    filename = os.path.join(os.path.dirname(__file__), "grader.conf")
    return confreader.read_config(filename)


def get_scope(problems, args, config):
    tasks = {}
    problems_to_run = [
        problem
        for problem in problems
        if args.problem is None or args.problem == problem.name
    ]

    for problem in problems_to_run:
        tasks[problem] = {}

        solutions_to_run = [
            solution
            for solution in problem.solutions
            if args.author is None or args.author == solution.author
        ]
        testcases_to_run = [
            testcase
            for testcase in problem.testcases
            if args.testcase is None or args.testcase == testcase.name
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
                adapter.run(testrun)
                verifier = create_verifier(testrun)
                is_correct = verifier.verify(testrun)

            except TestRunPrematureTerminationError as e:
                testrun.record_end_time()
                testrun.result = e.result

            if isinstance(testrun.result, TestRunCorrectAnswerResult):
                testrun.result.score = testrun.testcase.score
            else:
                testrun.result.score = 0

        except Exception as e:
            testrun.record_end_time()
            testrun.result = TestRunInternalErrorResult(e)

        time_elapsed = testrun.get_elapsed_milliseconds()
        print "-> {testrun.result}, Time: {time_elapsed} ms".format(**locals())
        testruns.append(testrun)

    return testruns


def create_adapter(solution):
    if solution.language == "java":
        return JavaSolutionAdapter(solution)
    return BaseSolutionAdapter(solution)


def create_verifier(testrun):
    verifier_class = testrun.solution.problem.config.get_safe("verifier", default_value="AnswerVerifier")
    verifier = globals()[verifier_class]
    return verifier()


def produce_report(testruns):
    pass
