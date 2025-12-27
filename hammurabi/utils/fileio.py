import re


def read_entire_file(filename):
    with open(filename, encoding="utf-8") as f:
        return f.read()


def write_entire_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def grep_value_from_file(filename, regex_pattern, group_num=0):
    regex = re.compile(regex_pattern)
    with open(filename, encoding="utf-8") as f:
        for line in f:
            match = regex.search(line)
            if match:
                return match.group(group_num)

    return None
