"""Solution runners for executing solutions."""

from __future__ import annotations

from hammurabi.grader.runners.base import BaseSolutionRunner
from hammurabi.grader.runners.subproc import SubprocessSolutionRunner

__all__ = [
    "BaseSolutionRunner",
    "SubprocessSolutionRunner",
    "registered_runners",
]

# Registry mapping runner names to classes
registered_runners: dict[str, type[BaseSolutionRunner]] = {
    "BaseSolutionRunner": BaseSolutionRunner,
    "SubprocessSolutionRunner": SubprocessSolutionRunner,
}
