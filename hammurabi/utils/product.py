"""Product information and banner display utilities."""

from hammurabi.utils import laws

version: tuple[int, int, int] = (0, 4, 0)

banner: list[str] = [
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

_terminal_width: int = 80


def get_version_string() -> str:
    """Return the version as a formatted string."""
    major, minor, patch = version
    return f"{major:d}.{minor:d}.{patch:d}"


def get_banner() -> list[str]:
    """Generate the application banner with version and a random law."""
    header_line_index = 2
    law_line_index = 4

    banner[header_line_index] = _expand_banner_line(
        banner[header_line_index], "Hammurabi v" + get_version_string()
    )

    random_law = laws.get_random_law()
    wrapped_law = _wrap_string(random_law, _terminal_width - len(banner[law_line_index]))

    for index, line in enumerate(wrapped_law):
        if index + law_line_index < len(banner):
            banner[index + law_line_index] = _expand_banner_line(
                banner[index + law_line_index], line
            )

    banner.append("")
    return banner


def print_banner() -> None:
    """Print the application banner to stdout."""
    banner_lines = get_banner()
    for line in banner_lines:
        print(line)


def _expand_banner_line(line: str, expansion_text: str) -> str:
    """Add expansion text to the right side of a banner line."""
    spare_width = _terminal_width - len(line) - len(expansion_text)
    spacer = " " * (spare_width // 2)
    return f"{line}{spacer}{expansion_text}{spacer}"


def _wrap_string(string: str, width: int) -> list[str]:
    """Wrap a string to fit within a given width."""
    wrapped_lines: list[str] = [""]
    words = string.split()

    for word in words:
        if len(wrapped_lines[-1]) + len(word) + 1 > width:
            wrapped_lines.append("")
        wrapped_lines[-1] += " " + word

    for index, line in enumerate(wrapped_lines):
        wrapped_lines[index] += " " * (width - len(line))

    return wrapped_lines
