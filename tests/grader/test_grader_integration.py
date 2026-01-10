"""Integration tests for the grader module."""

from __future__ import annotations

import pickle
import subprocess
from pathlib import Path


class TestGraderIntegration:
    """Integration tests that run the full grading process."""

    def test_correct_solutions_pass_all_testcases(
        self, grader_language_test_environment: tuple[str, str, str]
    ):
        """Correct solutions should pass all testcases for all languages."""
        config_file_path, _problem_dir_path, report_dir_path = grader_language_test_environment

        grader_cmd = f'python -m hammurabi grade --conf "{config_file_path}"'
        exitcode = subprocess.call(grader_cmd, shell=True)

        assert exitcode == 0, "Grader terminated with non-zero exit code."

        testrun_pickle_file = Path(report_dir_path) / "testrun" / "testruns.pickle"
        assert testrun_pickle_file.exists(), "Pickled testrun file not found."

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

    def test_faulty_solutions_report_proper_errors(
        self, grader_verification_test_environment: tuple[str, str, str]
    ):
        """Faulty solutions should report the correct error types."""
        config_file_path, _problem_dir_path, report_dir_path = grader_verification_test_environment

        grader_cmd = f'python -m hammurabi grade --conf "{config_file_path}"'
        exitcode = subprocess.call(grader_cmd, shell=True)

        assert exitcode == 0, "Grader terminated with non-zero exit code."

        testrun_pickle_file = Path(report_dir_path) / "testrun" / "testruns.pickle"
        assert testrun_pickle_file.exists(), "Pickled testrun file not found."

        with open(testrun_pickle_file, "rb") as pickle_file:
            testruns = pickle.load(pickle_file)

        expected_results_for_author = {
            "charlie-cpp-w": "W",
            "chris-csharp-t": "T",
            "cindy-c": "E",
            "jane-java-e": "E",
            "john-js-r": "R",
            "peter-python-m": "N",
            "rose-ruby-f": "F",
        }

        for author, result_code in expected_results_for_author.items():
            message = f"The solution '{author}' should have been verified as '[{result_code}]'."
            assert all(
                testrun.result.status_code == result_code
                for testrun in testruns
                if testrun.solution.author == author
            ), message
