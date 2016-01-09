import pytest
import os
import hammurabi.utils.fileio as fileio


sample_file_lines = [
    "abc 012 abcd 01234",
    "abcde 01234 abcdef 012345"
]


@pytest.fixture()
def sample_file_path_for_reading(tmpdir):
    file_path = tmpdir.join("sample_read_file.txt")
    filename = file_path.strpath

    content_to_write = os.linesep.join(sample_file_lines)
    with open(filename, "w") as sample_file:
        sample_file.write(content_to_write)

    return filename


@pytest.fixture()
def sample_file_path_for_writing(tmpdir):
    file_path = tmpdir.join("sample_write_file.txt")
    filename = file_path.strpath
    return filename


def test_read_entire_file_reads_all_lines(sample_file_path_for_reading):
    # Act
    content = fileio.read_entire_file(sample_file_path_for_reading).splitlines()

    # Assert
    assert content == sample_file_lines


def test_write_entire_file_reads_same_content(sample_file_path_for_writing):
    # Arrange
    content_to_write = os.linesep.join(sample_file_lines)

    # Act
    fileio.write_entire_file(sample_file_path_for_writing, content_to_write)
    content_read = fileio.read_entire_file(sample_file_path_for_writing)

    # Assert
    assert content_read == content_to_write


def test_grep_value_from_file_no_text_matched_returns_none(sample_file_path_for_reading):
    # Act
    value = fileio.grep_value_from_file(sample_file_path_for_reading, "I do not exist")

    # Assert
    assert value is None


def test_grep_value_from_file_no_group_specified_returns_full_match(sample_file_path_for_reading):
    # Act
    value = fileio.grep_value_from_file(sample_file_path_for_reading, r"(\w+) (\d+)")

    # Assert
    assert value == "abc 012"


def test_grep_value_from_file_group_specified_returns_only_that_group(sample_file_path_for_reading):
    # Act
    value = fileio.grep_value_from_file(sample_file_path_for_reading, r"(\w+) (\d+)", group_num=2)

    # Assert
    assert value == "012"
