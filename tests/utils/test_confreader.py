"""Tests for configuration file reader."""

import json

import pytest

from hammurabi.grader.config import GraderConfig
from hammurabi.grader.config import ProblemConfig
from hammurabi.utils import confreader

sample_grader_config = """
{
    "locations": {
        "problem_root": "problems",
        "report_root": "reports"
    }
}
"""

sample_problem_config = """
{
    "verifier": "CustomVerifier",
    "problem_input_file": "input.txt"
}
"""

invalid_config_content = """
{
    "locations": }}}
}
"""


@pytest.fixture
def filename_for_sample_grader_config(tmpdir):
    file_path = tmpdir.join("grader.conf")
    filename = file_path.strpath

    with open(filename, "w", encoding="utf-8") as f:
        f.write(sample_grader_config)

    return filename


@pytest.fixture
def filename_for_sample_problem_config(tmpdir):
    file_path = tmpdir.join("problem.conf")
    filename = file_path.strpath

    with open(filename, "w", encoding="utf-8") as f:
        f.write(sample_problem_config)

    return filename


@pytest.fixture
def filename_for_invalid_config(tmpdir):
    file_path = tmpdir.join("config_invalid.conf")
    filename = file_path.strpath

    with open(filename, "w", encoding="utf-8") as f:
        f.write(invalid_config_content)

    return filename


@pytest.fixture
def non_existent_filename(tmpdir):
    return tmpdir.join("i_do_not_exist.conf").strpath


def test_read_grader_config_given_invalid_json_throws(filename_for_invalid_config):
    with pytest.raises(json.JSONDecodeError):
        confreader.read_grader_config(filename_for_invalid_config)


def test_read_grader_config_given_nonexistent_file_throws(non_existent_filename):
    with pytest.raises(FileNotFoundError):
        confreader.read_grader_config(non_existent_filename)


def test_read_grader_config_given_valid_json_returns_config(filename_for_sample_grader_config):
    config = confreader.read_grader_config(filename_for_sample_grader_config)

    assert isinstance(config, GraderConfig)
    assert config.locations.problem_root == "problems"
    assert config.locations.report_root == "reports"


def test_read_problem_config_given_valid_json_returns_config(filename_for_sample_problem_config):
    config = confreader.read_problem_config(filename_for_sample_problem_config)

    assert isinstance(config, ProblemConfig)
    assert config.verifier == "CustomVerifier"
    assert config.problem_input_file == "input.txt"


def test_read_problem_config_given_nonexistent_file_throws(non_existent_filename):
    with pytest.raises(FileNotFoundError):
        confreader.read_problem_config(non_existent_filename)
