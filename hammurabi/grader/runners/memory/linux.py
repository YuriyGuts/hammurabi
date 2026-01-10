"""Linux memory limiter using resource.setrlimit."""

from __future__ import annotations

import resource
import subprocess
from collections.abc import Callable

from hammurabi.grader.runners.memory.base import BaseMemoryLimiter


class LinuxMemoryLimiter(BaseMemoryLimiter):
    """Memory limiter using Linux resource limits (setrlimit).

    Uses RLIMIT_AS to limit virtual address space, which is reliably
    enforced by the kernel.
    """

    def get_preexec_fn(self) -> Callable[[], None]:
        """Return preexec_fn that sets RLIMIT_AS.

        Returns
        -------
        Callable[[], None]
            Function that sets the memory limit before exec.
        """
        limit_bytes = self.memory_limit_bytes

        def set_memory_limit() -> None:
            # RLIMIT_AS limits virtual memory (address space).
            # This is more reliable than RLIMIT_DATA for catching malloc failures.
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))

        return set_memory_limit

    def attach_to_process(self, proc: subprocess.Popen) -> None:
        """No-op on Linux - limits are set via preexec_fn."""

    def start_monitoring(self, proc: subprocess.Popen, on_exceeded: Callable[[], None]) -> None:
        """No-op on Linux - kernel enforces limits via setrlimit.

        Note: On Linux, the kernel will kill the process with SIGKILL
        when it tries to allocate beyond the limit. The process receives
        an ENOMEM error from malloc/mmap.
        """

    def stop_monitoring(self) -> None:
        """No-op on Linux."""
