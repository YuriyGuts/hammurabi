import datetime
import os
import socket
import hammurabi.utils.confreader as confreader
import hammurabi.grader.discovery as discovery

from hammurabi.grader.runners.runner import SolutionRunner


def grade(args):
    config = read_config()
    apply_locations_to_config(config)
    problems = discovery.discover_problems(config)

    testruns = []

    for problem in problems:

        if args.problem is None or problem.name == args.problem:
            print "Judging problem: {problem.name}".format(**locals())
            print "=" * 75

            for solution in problem.solutions:
                if args.author is None or solution.author == args.author:
                    print
                    print "Judging solution:   Author: {solution.author}   Language: {solution.language}".format(**locals())
                    print "-" * 75

                    print "Compiling..."
                    runner = create_runner(solution, config)
                    runner.prepare()

                    for testcase in problem.testcases:
                        print "Running test case: {testcase.name} (max score: {testcase.score}).".format(**locals())
                        testrun = runner.run(testcase)
                        testruns.append(testrun)

    return testruns


def read_config():
    filename = os.path.join(os.path.dirname(__file__), "grader.conf")
    return confreader.read_config(filename)


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


def create_runner(solution, config):
    return SolutionRunner(solution, config)
