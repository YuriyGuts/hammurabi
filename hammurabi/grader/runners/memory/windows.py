"""Windows memory limiter using polling."""

from __future__ import annotations

from hammurabi.grader.runners.memory.fallback import PollingMemoryLimiter


class WindowsMemoryLimiter(PollingMemoryLimiter):
    """Memory limiter using polling via psutil.

    On Windows, we use the same polling-based approach as the fallback
    implementation. This is more reliable than Job Objects when using
    `shell=True` because:

    1. Job Objects have race conditions with child process creation.
    2. Per-process memory limits don't work well with `cmd.exe` + children.
    3. Job Objects can interfere with JVM and other runtimes that manage
       their own memory (causing errors like `ERROR_COMMITMENT_LIMIT`).

    The polling approach reliably monitors and enforces memory limits
    across all process types.
    """
