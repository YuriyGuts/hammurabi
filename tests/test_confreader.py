import pytest
import hammurabi.utils.confreader as confreader
from hammurabi.utils.dictview import ObjectDictView


sample_config_content = """
{
    "locations": {
        "problem_root": "problems",
        "report_root": "reports"
    }
}
"""

invalid_config_content = """
{
    "locations": }}}
}
"""


@pytest.fixture()
def filename_for_sample_valid_config(tmpdir):
    file_path = tmpdir.join("config.conf")
    filename = file_path.strpath

    with open(filename, "w") as sample_config:
        sample_config.write(sample_config_content)

    return filename


@pytest.fixture()
def filename_for_invalid_config(tmpdir):
    file_path = tmpdir.join("config_invalid.conf")
    filename = file_path.strpath

    with open(filename, "w") as invalid_config:
        invalid_config.write(invalid_config_content)

    return filename


@pytest.fixture()
def non_existent_filename(tmpdir):
    return tmpdir.join("i_do_not_exist.conf").strpath


def test_read_config_given_invalid_json_throws(filename_for_invalid_config):
    # Assert
    with pytest.raises(Exception):
        config = confreader.read_config(filename_for_invalid_config)


def test_read_config_given_nonexistent_file_throws(non_existent_filename):
    # Assert
    with pytest.raises(Exception):
        config = confreader.read_config(non_existent_filename)


def test_read_config_given_valid_json_returns_nested_objects(filename_for_sample_valid_config):
    # Act
    config = confreader.read_config(filename_for_sample_valid_config)

    # Assert
    assert len(vars(config)) == 1
    assert config.locations.problem_root == "problems"
    assert config.locations.report_root == "reports"
