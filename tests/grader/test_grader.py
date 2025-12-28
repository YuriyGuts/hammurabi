import json
import os
import pickle
import platform
import shutil
import subprocess

import pytest


def generate_hammurabi_environment(tmpdir, template_problem_dir):
    # Go up one level from tests/grader to tests/ to find test problem directories
    source_problem_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), template_problem_dir)
    )
    target_problem_dir = os.path.join(tmpdir.strpath, "problems")
    shutil.copytree(source_problem_dir, target_problem_dir)

    problem_dir_path = target_problem_dir
    report_dir_path = tmpdir.mkdir("reports").strpath
    config_file_path = tmpdir.join("grader.conf").strpath

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
        conf.write(json.dumps(config, indent=4))

    return config_file_path, problem_dir_path, report_dir_path


@pytest.fixture
def grader_language_test_environment(tmpdir):
    return generate_hammurabi_environment(tmpdir, "fixtures/problems_for_language_tests")


@pytest.fixture
def grader_verification_test_environment(tmpdir):
    return generate_hammurabi_environment(tmpdir, "fixtures/problems_for_verification_tests")


def test_all_languages_given_correct_solutions_pass_all_testcases(grader_language_test_environment):
    # Arrange
    config_file_path, _problem_dir_path, report_dir_path = grader_language_test_environment

    # Act
    grader_cmd = f'python -m hammurabi grade --conf "{config_file_path}"'
    exitcode = subprocess.call(grader_cmd, shell=True)

    # Assert
    assert exitcode == 0, "Grader terminated with non-zero exit code."

    testrun_pickle_file = os.path.abspath(
        os.path.join(report_dir_path, "testrun", "testruns.pickle")
    )
    assert os.path.exists(testrun_pickle_file), "Pickled testrun file not found."

    testruns = []
    with open(testrun_pickle_file, "rb") as pickle_file:
        testruns = pickle.load(pickle_file)

    expected_testrun_length = 70
    assert len(testruns) == expected_testrun_length, (
        f"Could not find results for {expected_testrun_length - len(testruns)} "
        f"testruns out of {len(testruns)}."
    )

    unique_languages = [testrun.solution.language for testrun in testruns]
    for language in unique_languages:
        failed_testruns_for_language = [
            testrun
            for testrun in testruns
            if testrun.solution.language == language and testrun.result.status_code != "C"
        ]
        assert len(failed_testruns_for_language) == 0, (
            f"Correct solution in '{language}' graded as "
            f"'{failed_testruns_for_language[0].result.status}'."
        )


def test_all_languages_given_faulty_solutions_report_proper_errors(
    grader_verification_test_environment,
):
    # Arrange
    config_file_path, _problem_dir_path, report_dir_path = grader_verification_test_environment

    # Act
    grader_cmd = f'python -m hammurabi grade --conf "{config_file_path}"'
    exitcode = subprocess.call(grader_cmd, shell=True)

    # Assert
    assert exitcode == 0, "Grader terminated with non-zero exit code."

    testrun_pickle_file = os.path.abspath(
        os.path.join(report_dir_path, "testrun", "testruns.pickle")
    )
    assert os.path.exists(testrun_pickle_file), "Pickled testrun file not found."

    testruns = []
    with open(testrun_pickle_file, "rb") as pickle_file:
        testruns = pickle.load(pickle_file)

    expected_results_for_author = {
        "charlie-cpp-w": "W",
        "chris-csharp-t": "T",
        "cindy-c": "E",
        "jane-java-e": "E",
        "john-js-r": "R",
        "peter-python-m": "M",
        "rose-ruby-f": "F",
    }

    for author, result_code in expected_results_for_author.items():
        message = f"The solution '{author}' should have been verified as '[{result_code}]'."
        assert all(
            testrun.result.status_code == result_code
            for testrun in testruns
            if testrun.solution.author == author
        ), message
