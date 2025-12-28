"""Typed configuration models using Pydantic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class TimeLimitsConfig(BaseModel):
    """Time limits per programming language in seconds."""

    c: float = 4.0
    cpp: float = 4.0
    csharp: float = 6.0
    java: float = 8.0
    javascript: float = 20.0
    php: float = 18.0
    python: float = 20.0
    ruby: float = 20.0
    scala: float = 14.0

    def get_for_language(self, language: str | None, default: float = 20.0) -> float:
        """Get the time limit for a specific language."""
        if language is None:
            return default
        return getattr(self, language, default)


class LimitsConfig(BaseModel):
    """Resource limits for solution execution."""

    memory: int = 512
    time: TimeLimitsConfig = Field(default_factory=TimeLimitsConfig)
    time_limit_multiplier: float = 1.0


class LocationsConfig(BaseModel):
    """File system locations for problems and reports."""

    problem_root: str = "grader/problems"
    report_root: str = "grader/reports"
    report_folder_template: str = "testrun-{dt:%Y%m%d-%H%M%S-%f}-{hostname}"


class RunnerConfig(BaseModel):
    """Solution runner configuration."""

    name: str = "SubprocessSolutionRunner"
    params: dict[str, Any] = Field(default_factory=dict)


class SecurityConfig(BaseModel):
    """Security settings for output reporting."""

    report_stdout: bool = True
    report_stderr: bool = True


class ReportingConfig(BaseModel):
    """Reporting banners and settings."""

    alert_banner: str = ""
    warning_banner: str = ""
    info_banner: str = ""


class GraderConfig(BaseModel):
    """Main grader configuration loaded from grader.conf."""

    locations: LocationsConfig = Field(default_factory=LocationsConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    runner: RunnerConfig = Field(default_factory=RunnerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)

    # Computed paths (set by apply_locations)
    problem_root_dir: str = ""
    report_root_dir: str = ""
    report_output_dir: str = ""

    @classmethod
    def from_file(cls, path: str | Path) -> GraderConfig:
        """Load configuration from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def merge_with(self, other: ProblemConfig) -> ProblemConfig:
        """
        Create a ProblemConfig by merging this grader config with problem-specific overrides.

        The problem config values take precedence over grader config values.
        """
        # Start with grader config values
        merged_data: dict[str, Any] = {
            "locations": self.locations.model_dump(),
            "limits": self.limits.model_dump(),
            "runner": self.runner.model_dump(),
            "security": self.security.model_dump(),
            "reporting": self.reporting.model_dump(),
            "problem_root_dir": self.problem_root_dir,
            "report_root_dir": self.report_root_dir,
            "report_output_dir": self.report_output_dir,
        }

        # Deep merge with problem config overrides
        other_data = other.model_dump(exclude_unset=True)
        _deep_merge(merged_data, other_data)

        return ProblemConfig.model_validate(merged_data)


class ProblemConfig(BaseModel):
    """
    Problem-specific configuration.

    Inherits from GraderConfig but adds problem-specific fields.
    """

    # Inherited from GraderConfig
    locations: LocationsConfig = Field(default_factory=LocationsConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    runner: RunnerConfig = Field(default_factory=RunnerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)

    # Computed paths (inherited)
    problem_root_dir: str = ""
    report_root_dir: str = ""
    report_output_dir: str = ""

    # Problem-specific fields
    verifier: str = "AnswerVerifier"
    problem_input_file: str | None = None
    problem_output_file: str | None = None
    testcase_score: dict[str, int] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> ProblemConfig:
        """Load the problem configuration from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def get_testcase_score(self, testcase_name: str, default: int = 1) -> int:
        """Get the score for a specific test case."""
        return self.testcase_score.get(testcase_name, default)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """
    Deep merge override into base dict, modifying base in place.

    Override values take precedence. Nested dicts are merged recursively.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
