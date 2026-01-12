"""Command-line interface for the Hammurabi grader."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hammurabi.grader import adapters
from hammurabi.grader import grader
from hammurabi.utils import product

ERROR_INVALID_ARGS = 1

# For printing expected/actual answers in problems involving long arithmetics.
sys.set_int_max_str_digits(100000)


def main() -> int | None:
    """
    Entry point for the Hammurabi CLI.

    Returns
    -------
    int | None
        Exit code, or None if successful.
    """
    args = _parse_command_line_args(sys.argv)
    _print_banner()

    if args.command == "grade":
        return _run_grader(args)

    if args.command == "languages":
        return _describe_languages()

    return None


def _parse_command_line_args(args: list[str]) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Parameters
    ----------
    args
        Command-line arguments (typically sys.argv).

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    top_level_parser = argparse.ArgumentParser(usage=f"{Path(args[0]).name} [COMMAND] [OPTIONS]")
    subparsers = top_level_parser.add_subparsers(
        title="Available commands", metavar="COMMAND", dest="command"
    )

    grade_command = "grade"
    grade_command_description = "Check one or more solutions."
    grade_command_parser = subparsers.add_parser(grade_command, help=grade_command_description)
    grade_command_parser.add_argument(
        "--conf", dest="conf", help="Use an alternative config file.", required=False
    )
    grade_command_parser.add_argument(
        "--problem",
        dest="problem",
        nargs="+",
        help="The names of the problems to grade.",
        required=False,
    )
    author_group = grade_command_parser.add_mutually_exclusive_group()
    author_group.add_argument(
        "--author",
        dest="author",
        nargs="+",
        help="Grade only these authors' solutions.",
        required=False,
    )
    author_group.add_argument(
        "--reference",
        dest="reference",
        action="store_true",
        help=(
            "Run only the reference solution "
            "(you can do this to produce the correct answers to a problem)."
        ),
        required=False,
    )
    grade_command_parser.add_argument(
        "--testcase",
        dest="testcase",
        nargs="+",
        help="Run only these particular test cases (by name, no extensions).",
        required=False,
    )

    languages_command = "languages"
    languages_command_description = "Describe the configured language compilers/interpreters."
    languages_command_parser = subparsers.add_parser(
        languages_command, help=languages_command_description
    )

    grade_command_parser.prog = grade_command_parser.prog.replace(
        " [COMMAND] [OPTIONS]", ""
    ).replace("usage: ", "")
    languages_command_parser.prog = languages_command_parser.prog.replace(
        " [COMMAND] [OPTIONS]", ""
    ).replace("usage: ", "")

    try:
        return top_level_parser.parse_args()
    except Exception:
        subparser_descriptions = [
            (grade_command, grade_command_description, grade_command_parser),
            (languages_command, languages_command_description, languages_command_parser),
        ]

        for command, description, parser in subparser_descriptions:
            print()
            print("-" * 30, "COMMAND:", command, "-" * 30)
            print(description)
            print()
            parser.print_help()

        sys.exit(ERROR_INVALID_ARGS)


def _print_banner() -> None:
    """Print the product banner."""
    product.print_banner()


def _run_grader(args: argparse.Namespace) -> int | None:
    """
    Run the grading process.

    Parameters
    ----------
    args
        Parsed command-line arguments.

    Returns
    -------
    int | None
        Exit code, or None if successful.
    """
    try:
        grader.grade(args)
        return None
    except (FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _describe_languages() -> int:
    """
    Print information about configured language adapters.

    Returns
    -------
    int
        Exit code (always 0).
    """
    registered = sorted(adapters.registered_adapters.items(), key=lambda item: item[0])
    for language, adapter in registered:
        print()
        print(f"--- {language} [{adapter.__name__}] ---")
        adapter.describe()

    return 0
