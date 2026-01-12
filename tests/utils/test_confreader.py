"""Tests for configuration file reader."""

import pytest
import yaml

from hammurabi.grader.config import GraderConfig
from hammurabi.grader.config import ProblemConfig
from hammurabi.utils import confreader

SAMPLE_GRADER_CONFIG = {
    "locations": {
        "problem_root": "problems",
        "report_root": "reports",
    }
}

SAMPLE_PROBLEM_CONFIG = {
    "verifier": "CustomVerifier",
    "problem_input_file": "input.txt",
}

INVALID_CONFIG_CONTENT = "locations: [[[invalid"


@pytest.fixture
def filename_for_sample_grader_config(tmpdir):
    file_path = tmpdir.join("hammurabi.yaml")
    filename = file_path.strpath

    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(SAMPLE_GRADER_CONFIG, f)

    return filename


@pytest.fixture
def filename_for_sample_problem_config(tmpdir):
    file_path = tmpdir.join("problem.yaml")
    filename = file_path.strpath

    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(SAMPLE_PROBLEM_CONFIG, f)

    return filename


@pytest.fixture
def filename_for_invalid_config(tmpdir):
    file_path = tmpdir.join("config_invalid.yaml")
    filename = file_path.strpath

    with open(filename, "w", encoding="utf-8") as f:
        f.write(INVALID_CONFIG_CONTENT)

    return filename


@pytest.fixture
def non_existent_filename(tmpdir):
    return tmpdir.join("i_do_not_exist.yaml").strpath


def test_read_grader_config_given_invalid_yaml_throws(filename_for_invalid_config):
    with pytest.raises(yaml.YAMLError):
        confreader.read_grader_config(filename_for_invalid_config)


def test_read_grader_config_given_nonexistent_file_throws(non_existent_filename):
    with pytest.raises(FileNotFoundError):
        confreader.read_grader_config(non_existent_filename)


def test_read_grader_config_given_valid_yaml_returns_config(filename_for_sample_grader_config):
    config = confreader.read_grader_config(filename_for_sample_grader_config)

    assert isinstance(config, GraderConfig)
    assert config.locations.problem_root == "problems"
    assert config.locations.report_root == "reports"


def test_read_problem_config_given_valid_yaml_returns_config(filename_for_sample_problem_config):
    config = confreader.read_problem_config(filename_for_sample_problem_config)

    assert isinstance(config, ProblemConfig)
    assert config.verifier == "CustomVerifier"
    assert config.problem_input_file == "input.txt"


def test_read_problem_config_given_nonexistent_file_throws(non_existent_filename):
    with pytest.raises(FileNotFoundError):
        confreader.read_problem_config(non_existent_filename)
