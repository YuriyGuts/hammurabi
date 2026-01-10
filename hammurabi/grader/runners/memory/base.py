"""Abstract base class for memory limit enforcement."""

from __future__ import annotations

import subprocess
from abc import ABC
from abc import abstractmethod
from collections.abc import Callable


class BaseMemoryLimiter(ABC):
    """Abstract base class for memory limit enforcement.

    Platform-specific implementations use different mechanisms:
    * Linux: `resource.setrlimit(RLIMIT_AS) via preexec_fn
    * Windows: Job Objects with memory limits
    * macOS/fallback: psutil polling
    """

    def __init__(self, memory_limit_mb: int) -> None:
        """Initialize the memory limiter.

        Parameters
        ----------
        memory_limit_mb
            Maximum memory allowed in megabytes.
        """
        self.memory_limit_mb = memory_limit_mb
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.peak_memory_mb: int | None = None

    @abstractmethod
    def get_preexec_fn(self) -> Callable[[], None] | None:
        """Return a function to be called in the subprocess before exec.

        Used for Linux setrlimit. Returns None on platforms that don't support it.

        Returns
        -------
        Callable[[], None] | None
            A function to set resource limits, or None.
        """

    @abstractmethod
    def attach_to_process(self, proc: subprocess.Popen) -> None:
        """Attach memory limiting to a running process.

        Used for Windows Job Objects. No-op on other platforms.

        Parameters
        ----------
        proc
            The subprocess to attach limits to.
        """

    @abstractmethod
    def start_monitoring(self, proc: subprocess.Popen, on_exceeded: Callable[[], None]) -> None:
        """Start background memory monitoring.

        Calls on_exceeded callback if memory limit is breached.

        Parameters
        ----------
        proc
            The subprocess to monitor.
        on_exceeded
            Callback to invoke when memory limit is exceeded.
        """

    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""

    def get_peak_memory_mb(self) -> int | None:
        """Return peak memory usage observed, if available.

        Returns
        -------
        int | None
            Peak memory in megabytes, or None if not tracked.
        """
        return self.peak_memory_mb
