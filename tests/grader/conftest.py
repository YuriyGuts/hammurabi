"""Shared fixtures for grader tests."""

from __future__ import annotations

import platform
import shutil
from pathlib import Path

import pytest
import yaml


def generate_hammurabi_environment(
    tmpdir: pytest.TempdirFactory, template_problem_dir: str
) -> tuple[str, str, str]:
    """Generate a test environment for hammurabi grader tests.

    Parameters
    ----------
    tmpdir
        Pytest tmpdir fixture.
    template_problem_dir
        Relative path to the template problem directory.

    Returns
    -------
    tuple[str, str, str]
        A tuple of (config_file_path, problem_dir_path, report_dir_path).
    """
    # Go up one level from tests/grader to tests/ to find test problem directories
    source_problem_dir = Path(__file__).parent / template_problem_dir
    source_problem_dir = source_problem_dir.resolve()
    target_problem_dir = Path(tmpdir.strpath) / "problems"
    shutil.copytree(source_problem_dir, target_problem_dir)

    problem_dir_path = str(target_problem_dir)
    report_dir_path = str(tmpdir.mkdir("reports"))
    config_file_path = str(tmpdir.join("hammurabi.yaml"))

    if platform.system() == "Windows":
        problem_dir_path = problem_dir_path.replace("\\", "/")
        report_dir_path = report_dir_path.replace("\\", "/")
        config_file_path = config_file_path.replace("\\", "/")

    config = {
        "locations": {
            "problem_root": problem_dir_path,
            "report_root": report_dir_path,
            "report_folder_template": "testrun",
        }
    }
    with open(config_file_path, "w", encoding="utf-8") as conf:
        yaml.dump(config, conf, default_flow_style=False)

    return config_file_path, problem_dir_path, report_dir_path


@pytest.fixture
def grader_language_test_environment(tmpdir: pytest.TempdirFactory) -> tuple[str, str, str]:
    """Create test environment for language tests."""
    return generate_hammurabi_environment(tmpdir, "fixtures/problems_for_language_tests")


@pytest.fixture
def grader_verification_test_environment(tmpdir: pytest.TempdirFactory) -> tuple[str, str, str]:
    """Create test environment for verification tests."""
    return generate_hammurabi_environment(tmpdir, "fixtures/problems_for_verification_tests")
