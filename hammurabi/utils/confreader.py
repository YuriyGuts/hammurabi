"""Configuration file reader."""

from pathlib import Path

from hammurabi.utils.config import GraderConfig
from hammurabi.utils.config import ProblemConfig


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
        print(f"Cannot load configuration file: {config_filename}")
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
        print(f"Cannot load configuration file: {config_filename}")
        print()
        raise
