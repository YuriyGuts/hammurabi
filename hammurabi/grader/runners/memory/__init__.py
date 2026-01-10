"""Memory limit enforcement module.

Provides platform-specific memory limiting for subprocess execution:
- Linux: resource.setrlimit(RLIMIT_AS) via preexec_fn
- Windows: Job Objects with memory limits
- macOS/fallback: psutil polling
"""

from __future__ import annotations

import platform

from hammurabi.grader.runners.memory.base import BaseMemoryLimiter
from hammurabi.grader.runners.memory.fallback import PollingMemoryLimiter

__all__ = ["create_memory_limiter", "BaseMemoryLimiter"]


def create_memory_limiter(memory_limit_mb: int) -> BaseMemoryLimiter:
    """Create the appropriate memory limiter for the current platform.

    Parameters
    ----------
    memory_limit_mb
        Maximum memory allowed in megabytes.

    Returns
    -------
    BaseMemoryLimiter
        A platform-appropriate memory limiter instance.
    """
    system = platform.system()

    if system == "Linux":
        from hammurabi.grader.runners.memory.linux import LinuxMemoryLimiter  # noqa: PLC0415

        return LinuxMemoryLimiter(memory_limit_mb)

    if system == "Windows":
        from hammurabi.grader.runners.memory.windows import WindowsMemoryLimiter  # noqa: PLC0415

        return WindowsMemoryLimiter(memory_limit_mb)

    # macOS and other platforms: use polling fallback
    return PollingMemoryLimiter(memory_limit_mb)
