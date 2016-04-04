import os
import pickle
import pytest
import shutil
import subprocess


@pytest.fixture()
def grader_language_tools_test_config(tmpdir):
    problem_dir_name = "grader_language_tools_test_problems"
    source_problem_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), problem_dir_name)
    target_problem_dir = os.path.join(tmpdir.strpath, "problems")
    shutil.copytree(source_problem_dir, target_problem_dir)

    problem_dir_path = target_problem_dir
    report_dir_path = tmpdir.mkdir("reports").strpath
    config_file_path = tmpdir.join("grader.conf").strpath

    with open(config_file_path, "w") as conf:
        conf.write("""
            {{
                "locations": {{
                    "problem_root": "{problem_dir_path}",
                    "report_root": "{report_dir_path}",
                    "report_folder_template": "testrun"
                }}
            }}
        """.format(**locals()))

    return (config_file_path, problem_dir_path, report_dir_path)


def test_all_languages_given_correct_solutions_pass_all_testcases(grader_language_tools_test_config):
    # Arrange
    config_file_path, problem_dir_path, report_dir_path = grader_language_tools_test_config
    hammurabi_entry_point = os.path.abspath(os.path.join(__file__, "..", "..", "hammurabi.py"))

    # Act
    grader_cmd = "python {hammurabi_entry_point} grade --conf {config_file_path}".format(**locals())
    exitcode = subprocess.call(grader_cmd, shell=True)

    # Assert
    assert exitcode == 0, "Grader terminated with non-zero exit code."

    testrun_pickle_file = os.path.abspath(os.path.join(report_dir_path, "testrun", "testruns.pickle"))
    assert os.path.exists(testrun_pickle_file), "Pickled testrun file not found."

    testruns = []
    with open(testrun_pickle_file, "rb") as pickle_file:
        testruns = pickle.load(pickle_file)

    expected_testrun_length = 60
    assert len(testruns) == expected_testrun_length, "Could not find results for %d testruns out of %d." % (expected_testrun_length, len(testruns))

    unique_languages = [testrun.solution.language for testrun in testruns]
    for language in unique_languages:
        failed_testruns_for_language = [
            testrun
            for testrun in testruns
            if testrun.solution.language == language and not testrun.result.is_correct()
        ]
        assert len(failed_testruns_for_language) == 0, "Correct solution in '%s' graded as '%s'." % (language, failed_testruns_for_language[0].result.status)
