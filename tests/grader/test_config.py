"""Tests for configuration models."""

import json
import tempfile
from pathlib import Path

from hammurabi.grader.config import GraderConfig
from hammurabi.grader.config import LimitsConfig
from hammurabi.grader.config import LocationsConfig
from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.config import ReportingConfig
from hammurabi.grader.config import RunnerConfig
from hammurabi.grader.config import SecurityConfig
from hammurabi.grader.config import TimeLimitsConfig
from hammurabi.grader.config import _deep_merge


class TestTimeLimitsConfig:
    def test_defaults(self):
        config = TimeLimitsConfig()
        assert config.python == 20.0
        assert config.java == 8.0
        assert config.c == 4.0

    def test_get_for_language_known(self):
        config = TimeLimitsConfig()
        assert config.get_for_language("python") == 20.0
        assert config.get_for_language("java") == 8.0

    def test_get_for_language_unknown(self):
        config = TimeLimitsConfig()
        assert config.get_for_language("unknown") == 20.0
        assert config.get_for_language("unknown", default=10.0) == 10.0

    def test_get_for_language_none(self):
        config = TimeLimitsConfig()
        assert config.get_for_language(None) == 20.0
        assert config.get_for_language(None, default=5.0) == 5.0

    def test_custom_values(self):
        config = TimeLimitsConfig(python=30.0, java=15.0)
        assert config.python == 30.0
        assert config.java == 15.0


class TestLimitsConfig:
    def test_defaults(self):
        config = LimitsConfig()
        assert config.memory == 512
        assert config.time_limit_multiplier == 1.0
        assert isinstance(config.time, TimeLimitsConfig)

    def test_nested_time_config(self):
        config = LimitsConfig(time=TimeLimitsConfig(python=30.0))
        assert config.time.python == 30.0
        assert config.time.java == 8.0


class TestLocationsConfig:
    def test_defaults(self):
        config = LocationsConfig()
        assert config.problem_root == "grader/problems"
        assert config.report_root == "grader/reports"
        assert "testrun-" in config.report_folder_template


class TestRunnerConfig:
    def test_defaults(self):
        config = RunnerConfig()
        assert config.name == "SubprocessSolutionRunner"
        assert config.params == {}

    def test_custom_runner(self):
        config = RunnerConfig(name="CustomRunner", params={"timeout": 30})
        assert config.name == "CustomRunner"
        assert config.params == {"timeout": 30}


class TestSecurityConfig:
    def test_defaults(self):
        config = SecurityConfig()
        assert config.report_stdout is True
        assert config.report_stderr is True


class TestReportingConfig:
    def test_defaults(self):
        config = ReportingConfig()
        assert config.alert_banner == ""
        assert config.warning_banner == ""
        assert config.info_banner == ""


class TestGraderConfig:
    def test_defaults(self):
        config = GraderConfig()
        assert isinstance(config.locations, LocationsConfig)
        assert isinstance(config.limits, LimitsConfig)
        assert isinstance(config.runner, RunnerConfig)

    def test_from_file(self):
        data = {
            "locations": {"problem_root": "custom/problems"},
            "limits": {"memory": 1024, "time": {"python": 30.0}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)

        try:
            config = GraderConfig.from_file(path)
            assert config.locations.problem_root == "custom/problems"
            assert config.limits.memory == 1024
            assert config.limits.time.python == 30.0
        finally:
            path.unlink()

    def test_merge_with_problem_config(self):
        grader = GraderConfig(limits=LimitsConfig(memory=512))
        problem = ProblemConfig(
            limits=LimitsConfig(memory=1024),
            verifier="CustomVerifier",
        )

        merged = grader.merge_with(problem)
        assert merged.limits.memory == 1024
        assert merged.verifier == "CustomVerifier"


class TestProblemConfig:
    def test_defaults(self):
        config = ProblemConfig()
        assert config.verifier == "AnswerVerifier"
        assert config.problem_input_file is None
        assert config.problem_output_file is None
        assert config.testcase_score == {}

    def test_get_testcase_score_existing(self):
        config = ProblemConfig(testcase_score={"test1": 10, "test2": 20})
        assert config.get_testcase_score("test1") == 10
        assert config.get_testcase_score("test2") == 20

    def test_get_testcase_score_missing(self):
        config = ProblemConfig(testcase_score={"test1": 10})
        assert config.get_testcase_score("unknown") == 1
        assert config.get_testcase_score("unknown", default=5) == 5

    def test_from_file(self):
        data = {
            "verifier": "CustomVerifier",
            "problem_input_file": "input.txt",
            "testcase_score": {"01": 5, "02": 10},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)

        try:
            config = ProblemConfig.from_file(path)
            assert config.verifier == "CustomVerifier"
            assert config.problem_input_file == "input.txt"
            assert config.get_testcase_score("01") == 5
        finally:
            path.unlink()


class TestDeepMerge:
    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        _deep_merge(base, override)
        assert base == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"outer": {"a": 1, "b": 2}}
        override = {"outer": {"b": 3, "c": 4}}
        _deep_merge(base, override)
        assert base == {"outer": {"a": 1, "b": 3, "c": 4}}

    def test_override_non_dict_with_dict(self):
        base = {"key": "value"}
        override = {"key": {"nested": True}}
        _deep_merge(base, override)
        assert base == {"key": {"nested": True}}

    def test_override_dict_with_non_dict(self):
        base = {"key": {"nested": True}}
        override = {"key": "value"}
        _deep_merge(base, override)
        assert base == {"key": "value"}

    def test_empty_override(self):
        base = {"a": 1, "b": 2}
        override = {}
        _deep_merge(base, override)
        assert base == {"a": 1, "b": 2}
