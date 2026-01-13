"""Terminal color and formatting utilities."""

from __future__ import annotations

import os
import sys
from enum import Enum
from functools import lru_cache
from typing import TextIO


class Color(Enum):
    """Standard ANSI foreground colors."""

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97


class Style(Enum):
    """ANSI text styles."""

    RESET = 0
    BOLD = 1
    DIM = 2


@lru_cache(maxsize=1)
def _detect_color_support() -> bool:
    """Detect if the terminal supports colors (cached)."""
    # Respect NO_COLOR convention (https://no-color.org/)
    if os.environ.get("NO_COLOR"):
        return False

    # Respect FORCE_COLOR for CI environments
    if os.environ.get("FORCE_COLOR"):
        return True

    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # Check TERM environment variable
    term = os.environ.get("TERM", "")
    return term != "dumb"


def supports_color(stream: TextIO = sys.stdout) -> bool:  # noqa: ARG001
    """Check if the given stream supports ANSI colors."""
    return _detect_color_support()


def colorize(text: str, color: Color | None = None, style: Style | None = None) -> str:
    """Apply color and/or style to text if colors are supported."""
    if not supports_color():
        return text

    codes = []
    if style is not None:
        codes.append(str(style.value))
    if color is not None:
        codes.append(str(color.value))

    if not codes:
        return text

    return f"\033[{';'.join(codes)}m{text}\033[0m"


def green(text: str) -> str:
    """Return text in green."""
    return colorize(text, Color.GREEN)


def red(text: str) -> str:
    """Return text in red."""
    return colorize(text, Color.RED)


def bright_red(text: str) -> str:
    """Return text in bright red."""
    return colorize(text, Color.BRIGHT_RED)


def yellow(text: str) -> str:
    """Return text in yellow."""
    return colorize(text, Color.YELLOW)


def cyan(text: str) -> str:
    """Return text in cyan."""
    return colorize(text, Color.CYAN)


def magenta(text: str) -> str:
    """Return text in magenta."""
    return colorize(text, Color.MAGENTA)


def bold(text: str) -> str:
    """Return text in bold."""
    return colorize(text, style=Style.BOLD)


def dim(text: str) -> str:
    """Return text in dim."""
    return colorize(text, style=Style.DIM)


def cyan_bold(text: str) -> str:
    """Return text in cyan and bold."""
    return colorize(text, Color.CYAN, Style.BOLD)
