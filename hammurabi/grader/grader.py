import os
import hammurabi.utils.confreader as confreader
import hammurabi.grader.discovery as discovery


def grade(args):
    config = read_config()
    problem_root_dir = get_problem_root_dir(config)
    problems = discovery.discover_problems(problem_root_dir)
    pass


def read_config():
    filename = os.path.join(os.path.dirname(__file__), "grader.conf")
    return confreader.read_config(filename)


def get_problem_root_dir(config):
    problem_root_dir = config.get_safe("locations/problem_root", default_value="problems")
    if not os.path.isabs(problem_root_dir):
        problem_root_dir = os.path.join(os.path.dirname(__file__), problem_root_dir)
        return problem_root_dir
