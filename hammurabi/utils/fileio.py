"""File I/O utilities."""

import re


def read_entire_file(filename: str) -> str:
    """Read and return the entire contents of a file."""
    with open(filename, encoding="utf-8") as f:
        return f.read()


def write_entire_file(filename: str, content: str) -> None:
    """Write content to a file, overwriting any existing content."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def grep_value_from_file(filename: str, regex_pattern: str, group_num: int = 0) -> str | None:
    """
    Search a file for the first line matching a regex pattern.

    Parameters
    ----------
    filename
        Path to the file to search.
    regex_pattern
        Regular expression pattern to match.
    group_num
        Capture group number to return (0 for entire match).

    Returns
    -------
    str | None
        The matched group, or None if no match found.
    """
    regex = re.compile(regex_pattern)
    with open(filename, encoding="utf-8") as f:
        for line in f:
            match = regex.search(line)
            if match:
                return match.group(group_num)

    return None
