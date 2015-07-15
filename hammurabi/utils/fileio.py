import re


def read_entire_file(filename):
    with open(filename, "r") as f:
        return f.read()


def grep_value_from_file(filename, regex_pattern, group_num=0):
    regex = re.compile(regex_pattern)
    with open(filename, "r") as f:
        for line in f:
            match = regex.search(line)
            if match:
                return match.group(group_num)

    return None
