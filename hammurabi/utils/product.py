import hammurabi.utils.laws as laws


version = (0, 3, 2)

banner = [
    r"       ,,--,,     ",
    r"      /______\    ",
    r"     /()_()_()\   ",
    r"    |----------|  ",
    r"    \/ ==  == \/  ",
    r"    /| (.)(.) |\  ",
    r"    \|  __)_  |/  ",
    r"     |./~__~\.|   ",
    r"    ||||....||||  ",
    r"    |**||||||**|  ",
    r"    |**|****|**|  ",
    r"    ||||||||||||  ",
    r"    |**|****|**|  ",
    r"    \||||||||||/  ",
    r"     \||****||/   ",
    r"      \||||||/    ",
]

_terminal_width = 80


def get_version_string():
    major, minor, patch = version
    return "{major:d}.{minor:d}.{patch:d}".format(**locals())


def get_banner():
    header_line_index = 2
    law_line_index = 4

    banner[header_line_index] = _expand_banner_line(banner[header_line_index], "Hammurabi v" + get_version_string())

    random_law = laws.get_random_law()
    wrapped_law = _wrap_string(random_law, _terminal_width - len(banner[law_line_index]))

    for (index, line) in enumerate(wrapped_law):
        if index + law_line_index < len(banner):
            banner[index + law_line_index] = _expand_banner_line(banner[index + law_line_index], line)

    banner.append("")
    return banner


def print_banner():
    banner = get_banner()
    for line in banner:
        print line


def _expand_banner_line(line, expansion_text):
    spare_width = _terminal_width - len(line) - len(expansion_text)
    spacer = " " * (spare_width // 2)
    return "{line}{spacer}{expansion_text}{spacer}".format(**locals())


def _wrap_string(string, width):
    wrapped_lines = [""]
    words = string.split()

    for word in words:
        if len(wrapped_lines[-1]) + len(word) + 1 > width:
            wrapped_lines.append("")
        wrapped_lines[-1] += " " + word

    for (index, line) in enumerate(wrapped_lines):
        wrapped_lines[index] += " " * (width - len(line))

    return wrapped_lines
