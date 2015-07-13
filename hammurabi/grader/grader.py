import os
import hammurabi.utils.confreader as confreader
import hammurabi.grader.discovery as discovery

from hammurabi.grader.runners.runner import SolutionRunner


def grade(args):
    config = read_config()
    problem_root_dir = get_problem_root_dir(config)
    problems = discovery.discover_problems(problem_root_dir)

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
                    runner = create_runner(config, solution)
                    runner.prepare()

                    for testcase in problem.testcases:
                        print "Running test case: {testcase.name} (max score: {testcase.score}).".format(**locals())
                        runner.run(testcase)


def read_config():
    filename = os.path.join(os.path.dirname(__file__), "grader.conf")
    return confreader.read_config(filename)


def get_problem_root_dir(config):
    problem_root_dir = config.get_safe("locations/problem_root", default_value="problems")
    if not os.path.isabs(problem_root_dir):
        problem_root_dir = os.path.join(os.path.dirname(__file__), problem_root_dir)
        return problem_root_dir


def create_runner(config, solution):
    return SolutionRunner(config, solution)
