"""Polling-based memory limiter for platforms without OS-level enforcement."""

from __future__ import annotations

import contextlib
import subprocess
import threading
from collections.abc import Callable

import psutil

from hammurabi.grader.runners.memory.base import BaseMemoryLimiter


class PollingMemoryLimiter(BaseMemoryLimiter):
    """Memory limiter using periodic polling via `psutil`.

    This is the fallback implementation for macOS and other platforms
    where OS-level memory enforcement is unreliable.
    """

    # 50ms polling interval.
    POLL_INTERVAL_SECONDS = 0.05

    def __init__(self, memory_limit_mb: int) -> None:
        """Initialize the polling memory limiter."""
        super().__init__(memory_limit_mb)
        self._stop_event = threading.Event()
        self._monitor_thread: threading.Thread | None = None

    def get_preexec_fn(self) -> Callable[[], None] | None:
        """Return None - polling doesn't use preexec."""
        return None

    def attach_to_process(self, proc: subprocess.Popen) -> None:
        """No-op - polling starts via start_monitoring."""

    def start_monitoring(self, proc: subprocess.Popen, on_exceeded: Callable[[], None]) -> None:
        """Start background thread that polls memory usage.

        Parameters
        ----------
        proc
            The subprocess to monitor.
        on_exceeded
            Callback to invoke when the memory limit is exceeded.
        """
        self._stop_event.clear()

        def monitor_loop() -> None:
            while not self._stop_event.is_set():
                try:
                    process = psutil.Process(proc.pid)
                    total_memory = self._get_total_memory_bytes(process)
                    total_memory_mb = total_memory // (1024 * 1024)

                    # Track peak memory
                    if self.peak_memory_mb is None or total_memory_mb > self.peak_memory_mb:
                        self.peak_memory_mb = total_memory_mb

                    if total_memory > self.memory_limit_bytes:
                        on_exceeded()
                        return

                except psutil.NoSuchProcess:
                    # Process ended
                    return
                except Exception:
                    # Continue monitoring despite errors
                    pass

                self._stop_event.wait(self.POLL_INTERVAL_SECONDS)

        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        self._stop_event.set()
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None

    def _get_total_memory_bytes(self, process: psutil.Process) -> int:
        """Get total RSS memory usage including all child processes.

        Parameters
        ----------
        process
            The parent process to measure.

        Returns
        -------
        int
            Total memory usage in bytes across all processes.
        """
        total = 0
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            total += process.memory_info().rss
            for child in process.children(recursive=True):
                with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                    total += child.memory_info().rss
        return total
