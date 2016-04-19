import codecs
import re


def read_entire_file(filename):
    with codecs.open(filename, "r", "utf-8") as f:
        return f.read()


def write_entire_file(filename, content):
    with codecs.open(filename, "w", "utf-8") as f:
        f.write(content)


def grep_value_from_file(filename, regex_pattern, group_num=0):
    regex = re.compile(regex_pattern)
    with codecs.open(filename, "r", "utf-8") as f:
        for line in f:
            match = regex.search(line)
            if match:
                return match.group(group_num)

    return None
