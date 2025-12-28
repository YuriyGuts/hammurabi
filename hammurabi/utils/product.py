"""Product information and banner display utilities."""

import shutil

from hammurabi.utils import laws

VERSION: tuple[int, int, int] = (0, 4, 0)

_BANNER_ART: tuple[str, ...] = (
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
)

_DEFAULT_TERMINAL_WIDTH: int = 80


def _get_terminal_width() -> int:
    """Get the current terminal width, with a sensible default."""
    return shutil.get_terminal_size(fallback=(_DEFAULT_TERMINAL_WIDTH, 24)).columns


def get_version_string() -> str:
    """Return the version as a formatted string."""
    major, minor, patch = VERSION
    return f"{major}.{minor}.{patch}"


def get_banner() -> list[str]:
    """Generate the application banner with version and a random law."""
    banner = list(_BANNER_ART)
    terminal_width = _get_terminal_width()
    header_line_index = 2
    law_line_index = 4

    banner[header_line_index] = _append_to_banner_line(
        banner[header_line_index], f" Hammurabi v{get_version_string()}"
    )

    random_law = laws.get_random_law()
    text_width = terminal_width - len(banner[law_line_index]) - 2  # 2 for padding
    wrapped_law = _wrap_string(random_law, text_width)

    for index, line in enumerate(wrapped_law):
        if index + law_line_index < len(banner):
            banner[index + law_line_index] = _append_to_banner_line(
                banner[index + law_line_index], line
            )

    banner.append("")
    return banner


def print_banner() -> None:
    """Print the application banner to stdout."""
    banner_lines = get_banner()
    for line in banner_lines:
        print(line)


def _append_to_banner_line(line: str, text: str) -> str:
    """Append text to the right side of a banner line with a small gap."""
    return f"{line}  {text}"


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
