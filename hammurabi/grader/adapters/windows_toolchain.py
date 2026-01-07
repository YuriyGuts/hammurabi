"""Windows C/C++ toolchain detection and configuration.

This module provides utilities for detecting and using C/C++ compilers on Windows.

It supports two toolchains:
1. MinGW-w64 (GCC) - Preferred, uses the same commands as Linux.
2. MSVC (Visual Studio Build Tools) - Fallback, requires `vswhere` detection.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path


class WindowsToolchain(Enum):
    """Available C/C++ toolchains on Windows."""

    MINGW = "mingw"
    MSVC = "msvc"


@dataclass
class ToolchainConfig:
    """Configuration for a detected toolchain."""

    toolchain: WindowsToolchain
    c_compiler: str
    cpp_compiler: str
    compile_prefix: str  # Commands to run before compilation (e.g., vcvarsall setup)
    c_flags: list[str]
    cpp_flags: list[str]
    link_output_flag: str  # Flag to specify output file


def _find_vswhere() -> Path | None:
    """Find vswhere.exe, which is used to locate Visual Studio installations.

    vswhere is installed by Visual Studio and Visual Studio Build Tools in a
    well-known location.
    """
    # Standard location for vswhere.
    program_files = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    vswhere_path = Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"

    if vswhere_path.exists():
        return vswhere_path

    # Also check if it's in PATH.
    vswhere_in_path = shutil.which("vswhere")
    if vswhere_in_path:
        return Path(vswhere_in_path)

    return None


def _find_vcvarsall() -> Path | None:
    """Find vcvarsall.bat using vswhere to locate Visual Studio installation."""
    vswhere = _find_vswhere()
    if not vswhere:
        return None

    try:
        # Query `vswhere` for the installation path.
        # `-latest`: Get the most recent installation.
        # `-products` *: Include Build Tools (not just full VS).
        # `-requires`: Ensure C++ tools are installed.
        # `-property installationPath`: Return only the path.
        result = subprocess.run(
            [
                str(vswhere),
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None

        install_path = Path(result.stdout.strip())
        vcvarsall = install_path / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"

        if vcvarsall.exists():
            return vcvarsall

    except (subprocess.TimeoutExpired, OSError):
        pass

    return None


def _check_mingw_available() -> bool:
    """Check if MinGW (gcc/g++) is available in PATH."""
    return shutil.which("gcc") is not None and shutil.which("g++") is not None


def _check_msvc_available() -> bool:
    """Check if MSVC (via `vcvarsall.bat`) is available."""
    return _find_vcvarsall() is not None


@lru_cache(maxsize=1)
def detect_toolchain() -> ToolchainConfig | None:
    """Detect available C/C++ toolchain on Windows.

    Returns the first available toolchain in order of preference:
    1. MinGW-w64 (GCC) - simpler, same commands as Linux
    2. MSVC (Visual Studio Build Tools) - Microsoft's official compiler

    Returns `None` if no toolchain is available.
    """
    # Try MinGW first (preferred for simplicity).
    if _check_mingw_available():
        return ToolchainConfig(
            toolchain=WindowsToolchain.MINGW,
            c_compiler="gcc",
            cpp_compiler="g++",
            compile_prefix="",
            c_flags=["--std=c99", "-O2"],
            cpp_flags=["-std=c++11", "-O3"],
            link_output_flag="-o",
        )

    # Try MSVC as a fallback.
    vcvarsall = _find_vcvarsall()
    if vcvarsall:
        # Use x64 architecture by default for modern systems.
        # The `compile_prefix` sets up the environment, then runs the command.
        setup_cmd = f'"{vcvarsall}" x64 >nul 2>&1 &&'
        return ToolchainConfig(
            toolchain=WindowsToolchain.MSVC,
            c_compiler="cl",
            cpp_compiler="cl",
            compile_prefix=setup_cmd,
            c_flags=["/nologo", "/Ox", "/EHsc"],
            cpp_flags=["/nologo", "/Ox", "/EHsc"],
            link_output_flag="/Fe:",  # MSVC output flag (colon is part of flag).
        )

    return None


def get_toolchain_description() -> str:
    """Get a human-readable description of the detected toolchain."""
    config = detect_toolchain()
    if config is None:
        return "No C/C++ toolchain detected"

    if config.toolchain == WindowsToolchain.MINGW:
        return "MinGW-w64 (GCC)"
    else:
        return "Microsoft Visual C++ (MSVC)"


def print_compiler_version() -> None:
    """Print the version information of the detected compiler."""
    config = detect_toolchain()
    if config is None:
        print("No C/C++ toolchain detected on Windows.")
        print("Install one of:")
        print("  - MinGW-w64: https://www.msys2.org/ (recommended)")
        print(
            "  - VS Build Tools: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022"
        )
        return

    if config.toolchain == WindowsToolchain.MINGW:
        subprocess.call("gcc --version", shell=True)
    else:
        # For MSVC, we need to set up the environment first
        vcvarsall = _find_vcvarsall()
        if vcvarsall:
            subprocess.call(f'"{vcvarsall}" x64 >nul 2>&1 && cl', shell=True)


def build_c_compile_command(sources: list[str], output_path: str) -> str:
    """
    Build the C compilation command for Windows.

    Raises
    ------
    RuntimeError
        If no toolchain is available.
    """
    config = detect_toolchain()
    if config is None:
        raise RuntimeError("No C/C++ toolchain available on Windows")

    quoted_sources = " ".join([f'"{s}"' for s in sources])
    flags = " ".join(config.c_flags)
    out_flag = config.link_output_flag

    if config.toolchain == WindowsToolchain.MINGW:
        return f'{config.c_compiler} {flags} {quoted_sources} {out_flag} "{output_path}"'
    else:
        # MSVC command with environment setup.
        prefix = config.compile_prefix
        compiler = config.c_compiler
        return f'{prefix} {compiler} {flags} {quoted_sources} {out_flag}"{output_path}"'


def build_cpp_compile_command(sources: list[str], output_path: str) -> str:
    """
    Build the C++ compilation command for Windows.

    Raises
    ------
    RuntimeError
        If no toolchain is available.
    """
    config = detect_toolchain()
    if config is None:
        raise RuntimeError("No C/C++ toolchain available on Windows")

    quoted_sources = " ".join([f'"{s}"' for s in sources])
    flags = " ".join(config.cpp_flags)
    out_flag = config.link_output_flag

    if config.toolchain == WindowsToolchain.MINGW:
        return f'{config.cpp_compiler} {flags} {quoted_sources} {out_flag} "{output_path}"'
    else:
        # MSVC command with environment setup.
        prefix = config.compile_prefix
        compiler = config.cpp_compiler
        return f'{prefix} {compiler} {flags} {quoted_sources} {out_flag}"{output_path}"'
