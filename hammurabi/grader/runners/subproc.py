"""Subprocess-based solution runner with timeout support."""

from __future__ import annotations

import contextlib
import subprocess
import threading
from collections.abc import Sequence

import psutil

from hammurabi.exceptions import SubprocessMemoryLimitError
from hammurabi.exceptions import SubprocessTimeoutError
from hammurabi.exceptions import TestRunPrematureTerminationError
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunMemoryExceededResult
from hammurabi.grader.model import TestRunTimeoutResult
from hammurabi.grader.runners.base import BaseSolutionRunner
from hammurabi.grader.runners.memory import create_memory_limiter


class SubprocessSolutionRunner(BaseSolutionRunner):
    """Runs solutions in a subprocess with timeout enforcement."""

    def __init__(self) -> None:
        super().__init__()

    def run(self, testrun: TestRun, cmd: Sequence[str]) -> None:
        """Run the command with time and memory limit enforcement."""
        config = testrun.solution.problem.config
        time_limit = config.limits.time.get_for_language(testrun.solution.language)
        multiplier = config.limits.time_limit_multiplier
        adjusted_time_limit = time_limit * multiplier

        try:
            self.run_command_with_time_and_ram_limits(testrun, cmd, adjusted_time_limit)
        except SubprocessTimeoutError as e:
            result = TestRunTimeoutResult(adjusted_time_limit)
            raise TestRunPrematureTerminationError(result) from e
        except SubprocessMemoryLimitError as e:
            result = TestRunMemoryExceededResult(
                memory_limit_mb=e.memory_limit_mb,
                peak_memory_mb=e.peak_memory_mb,
            )
            raise TestRunPrematureTerminationError(result) from e

    def run_command_with_time_and_ram_limits(
        self, testrun: TestRun, cmd: Sequence[str], timeout_sec: float
    ) -> int | None:
        """
        Execute a command in a subprocess with timeout and memory limit enforcement.

        Parameters
        ----------
        testrun
            The test run context.
        cmd
            Command to execute.
        timeout_sec
            Timeout in seconds.

        Returns
        -------
        int | None
            Exit code on natural completion.

        Raises
        ------
        SubprocessTimeoutError
            If the timeout expires before completion.
        SubprocessMemoryLimitError
            If the memory limit is exceeded.
        """
        timeout_occurred = threading.Event()
        memory_exceeded = threading.Event()
        kill_lock = threading.Lock()
        process_killed = threading.Event()

        # Get memory limit from testrun (default 512 MB)
        memory_limit_mb = testrun.memory_limit or 512
        memory_limiter = create_memory_limiter(memory_limit_mb)

        def do_kill_process(process: psutil.Process) -> None:
            with contextlib.suppress(psutil.NoSuchProcess):
                process.kill()

        def kill_process_tree() -> None:
            # Use lock to prevent concurrent termination attempts.
            with kill_lock:
                if process_killed.is_set():
                    return
                process_killed.set()
                with contextlib.suppress(psutil.NoSuchProcess):
                    process = psutil.Process(proc.pid)
                    for child_process in process.children(recursive=True):
                        do_kill_process(child_process)
                    do_kill_process(process)

        def timeout_handler() -> None:
            timeout_occurred.set()
            kill_process_tree()

        def memory_handler() -> None:
            memory_exceeded.set()
            kill_process_tree()

        assert testrun.stdout_filename is not None
        assert testrun.stderr_filename is not None
        with (
            open(testrun.stdout_filename, "w", encoding="utf-8") as stdout,
            open(testrun.stderr_filename, "w", encoding="utf-8") as stderr,
        ):
            testrun.record_lean_start_time()

            # Use `preexec_fn` for Linux memory limits.
            # Note: `preexec_fn` runs in the child after `fork` but before `exec`,
            # and our threading only starts after `Popen` returns, so this is safe.
            preexec_fn = memory_limiter.get_preexec_fn()

            proc = subprocess.Popen(
                cmd,
                shell=False,
                cwd=testrun.solution.root_dir,
                stdout=stdout,
                stderr=stderr,
                preexec_fn=preexec_fn,  # noqa: PLW1509
            )

            # Attach Windows Job Object if applicable.
            memory_limiter.attach_to_process(proc)

            # Start memory monitoring (for polling-based enforcement).
            memory_limiter.start_monitoring(proc, memory_handler)

            # Start timeout timer.
            timer = threading.Timer(timeout_sec, timeout_handler)
            timer.daemon = True
            timer.start()

            try:
                proc.communicate()
            finally:
                # Ensure cleanup always runs even if communicate() raises
                timer.cancel()
                memory_limiter.stop_monitoring()

            testrun.record_lean_end_time()

            # Check for memory exceeded (check first since it may have triggered).
            if memory_exceeded.is_set():
                raise SubprocessMemoryLimitError(
                    message=f"Process #{proc.pid} killed: memory limit exceeded",
                    memory_limit_mb=memory_limit_mb,
                    peak_memory_mb=memory_limiter.get_peak_memory_mb(),
                )

            if timeout_occurred.is_set():
                # Process killed by timer -> raise an exception.
                raise SubprocessTimeoutError(
                    message=f"Process #{proc.pid} killed after {timeout_sec} seconds",
                    timeout=timeout_sec,
                    exit_code=proc.returncode,
                )

            # Process completed naturally -> return the exit code.
            return proc.returncode
