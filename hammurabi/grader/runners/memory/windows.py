"""Windows memory limiter using Job Objects."""

from __future__ import annotations

import contextlib
import ctypes
import subprocess
from collections.abc import Callable

from hammurabi.grader.runners.memory.base import BaseMemoryLimiter

# Windows Job Object constants.
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

# Job Object information classes.
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9

# Process access rights.
PROCESS_SET_QUOTA = 0x0100
PROCESS_TERMINATE = 0x0001


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):  # noqa: N801
    """Windows JOBOBJECT_BASIC_LIMIT_INFORMATION structure."""

    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class IO_COUNTERS(ctypes.Structure):  # noqa: N801
    """Windows IO_COUNTERS structure."""

    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION_STRUCT(ctypes.Structure):  # noqa: N801
    """Windows JOBOBJECT_EXTENDED_LIMIT_INFORMATION structure."""

    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class WindowsMemoryLimiter(BaseMemoryLimiter):
    """Memory limiter using Windows Job Objects.

    Creates a Job Object with memory limits and assigns the process to it.
    The kernel will terminate the process if it exceeds the memory limit.
    """

    def __init__(self, memory_limit_mb: int) -> None:
        """Initialize the Windows memory limiter."""
        super().__init__(memory_limit_mb)
        self._job_handle: int | None = None

    def get_preexec_fn(self) -> Callable[[], None] | None:
        """Return None - Windows uses Job Objects after process creation."""
        return None

    def attach_to_process(self, proc: subprocess.Popen) -> None:
        """Create a Job Object and assign the process to it.

        Parameters
        ----------
        proc
            The subprocess to attach limits to.
        """
        try:
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

            # Create a Job Object.
            self._job_handle = kernel32.CreateJobObjectW(None, None)
            if not self._job_handle:
                return  # Fall back to polling if this fails.

            # Configure memory limit
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION_STRUCT()
            info.BasicLimitInformation.LimitFlags = (
                JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            info.ProcessMemoryLimit = self.memory_limit_bytes

            # Set the job object limits.
            success = kernel32.SetInformationJobObject(
                self._job_handle,
                JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                ctypes.byref(info),
                ctypes.sizeof(info),
            )
            if not success:
                kernel32.CloseHandle(self._job_handle)
                self._job_handle = None
                return

            # Assign the process to the job.
            process_handle = kernel32.OpenProcess(
                PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, proc.pid
            )
            if process_handle:
                kernel32.AssignProcessToJobObject(self._job_handle, process_handle)
                kernel32.CloseHandle(process_handle)
        except (AttributeError, OSError):
            # `windll` not available or other error - will fall back to polling.
            self._job_handle = None

    def start_monitoring(self, proc: subprocess.Popen, on_exceeded: Callable[[], None]) -> None:
        """No-op - Windows Job Objects handle enforcement automatically."""

    def stop_monitoring(self) -> None:
        """Clean up the Job Object handle."""
        if self._job_handle:
            with contextlib.suppress(AttributeError, OSError):
                ctypes.windll.kernel32.CloseHandle(self._job_handle)  # type: ignore[attr-defined]
            self._job_handle = None
