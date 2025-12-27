#!/usr/bin/env python

import argparse
import os
import subprocess
import sys


ERROR_INVALID_ARGS = 1


def main():
    bootstrap()
    args = parse_command_line_args(sys.argv)
    print_banner()

    if args.command == "grade":
        return run_grader(args)

    if args.command == "server":
        return run_server(args)

    if args.command == "languages":
        return describe_languages(args)


def bootstrap():
    # In scope of this process, add self to PYTHONPATH for the imports to work properly.
    current_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(current_dir)


def parse_command_line_args(args):
    top_level_parser = argparse.ArgumentParser(usage="{self} [COMMAND] [OPTIONS]".format(self=os.path.basename(args[0])))
    subparsers = top_level_parser.add_subparsers(title="Available commands", metavar="COMMAND", dest="command")

    grade_command = "grade"
    grade_command_description = "Check one or more solutions."
    grade_command_parser = subparsers.add_parser(grade_command, help=grade_command_description)
    grade_command_parser.add_argument(
        "--conf",
        dest="conf",
        help="Use an alternative config file.",
        required=False
    )
    grade_command_parser.add_argument(
        "--problem",
        dest="problem",
        nargs="+",
        help="The names of the problems to grade.",
        required=False
    )
    author_group = grade_command_parser.add_mutually_exclusive_group()
    author_group.add_argument(
        "--author",
        dest="author",
        nargs="+",
        help="Grade only these authors' solutions.",
        required=False
    )
    author_group.add_argument(
        "--reference",
        dest="reference",
        action="store_true",
        help="Run only the reference solution (you can do this to produce the correct answers to a problem).",
        required=False
    )
    grade_command_parser.add_argument(
        "--testcase",
        dest="testcase",
        nargs="+",
        help="Run only these particular test cases (by name, no extensions).",
        required=False
    )

    languages_command = "languages"
    languages_command_description = "Describe the configured language compilers/interpreters."
    languages_command_parser = subparsers.add_parser(languages_command, help=languages_command_description)

    server_command = "server"
    server_command_description = "Serve a Web application for submitting solutions."
    server_command_parser = subparsers.add_parser(server_command, help=server_command_description)
    server_command_parser.add_argument(
        "--address",
        dest="address",
        help="Address to listen on.",
        default="0.0.0.0",
        required=False
    )
    server_command_parser.add_argument(
        "--port",
        dest="port",
        help="Port to listen on.",
        default="4266",
        required=False
    )

    grade_command_parser.prog = grade_command_parser.prog.replace(" [COMMAND] [OPTIONS]", "").replace("usage: ", "")
    languages_command_parser.prog = languages_command_parser.prog.replace(" [COMMAND] [OPTIONS]", "").replace("usage: ", "")
    server_command_parser.prog = server_command_parser.prog.replace(" [COMMAND] [OPTIONS]", "").replace("usage: ", "")

    try:
        command_line_args = top_level_parser.parse_args()
        return command_line_args
    except:
        subparser_descriptions = [
            (grade_command, grade_command_description, grade_command_parser),
            (languages_command, languages_command_description, languages_command_parser),
            (server_command, server_command_description, server_command_parser)
        ]

        for command, description, parser in subparser_descriptions:
            print("")
            print("-" * 30, "COMMAND:", command, "-" * 30)
            print(description)
            print("")
            parser.print_help()

        sys.exit(ERROR_INVALID_ARGS)


def print_banner():
    import hammurabi.utils.product as product
    product.print_banner()


def run_grader(args):
    import hammurabi.grader.grader as grader
    return grader.grade(args)


def describe_languages(args):
    import hammurabi.grader.adapters as adapters

    registered_adapters = sorted(adapters.registered_adapters.items(), key=lambda tuple: tuple[0])
    for language, adapter in registered_adapters:
        print()
        print("--- {0} [{1}] ---".format(language, adapter.__name__))
        adapter.describe()

    return 0


def run_server(args):
    current_dir = os.getcwd()
    manage_script_path = os.path.join(current_dir, "hammurabi", "web", "manage.py")
    server_run_command = "python {manage_script_path} runserver {args.address}:{args.port}".format(**locals())
    return subprocess.call(server_run_command, shell=True)


if __name__ == "__main__":
    main()
