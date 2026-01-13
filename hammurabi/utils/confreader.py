"""Configuration file reader."""

from pathlib import Path

from hammurabi.grader.config import GraderConfig
from hammurabi.grader.config import ProblemConfig
from hammurabi.utils import terminal


def read_grader_config(config_filename: str | Path) -> GraderConfig:
    """
    Read a grader configuration file.

    Raises
    ------
    Exception
        If the file cannot be read or parsed.
    """
    try:
        return GraderConfig.from_file(config_filename)
    except Exception:
        print(terminal.red(f"Cannot load configuration file: {config_filename}"))
        print()
        raise


def read_problem_config(config_filename: str | Path) -> ProblemConfig:
    """
    Read a problem configuration file.

    Raises
    ------
    Exception
        If the file cannot be read or parsed.
    """
    try:
        return ProblemConfig.from_file(config_filename)
    except Exception:
        print(terminal.red(f"Cannot load configuration file: {config_filename}"))
        print()
        raise
