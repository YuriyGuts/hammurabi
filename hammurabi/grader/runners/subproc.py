"""Subprocess-based solution runner with timeout support."""

from __future__ import annotations

import contextlib
import subprocess
import threading

import psutil

from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunTimeoutResult
from hammurabi.grader.runners.base import BaseSolutionRunner
from hammurabi.utils.exceptions import SubprocessTimeoutError
from hammurabi.utils.exceptions import TestRunPrematureTerminationError


class SubprocessSolutionRunner(BaseSolutionRunner):
    """Runs solutions in a subprocess with timeout enforcement."""

    def __init__(self) -> None:
        super().__init__()

    def run(self, testrun: TestRun, cmd: str) -> None:
        """Run the command with time limit enforcement."""
        config = testrun.solution.problem.config
        time_limit = config.limits.time.get_for_language(testrun.solution.language)
        multiplier = config.limits.time_limit_multiplier
        adjusted_time_limit = time_limit * multiplier

        try:
            self.run_command_with_timeout(testrun, cmd, adjusted_time_limit)
        except SubprocessTimeoutError as e:
            result = TestRunTimeoutResult(adjusted_time_limit)
            raise TestRunPrematureTerminationError(result) from e

    def run_command_with_timeout(
        self, testrun: TestRun, cmd: str, timeout_sec: float
    ) -> int | None:
        """
        Execute a command in a subprocess with timeout enforcement.

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
        """

        def do_kill_process(process: psutil.Process) -> None:
            with contextlib.suppress(psutil.NoSuchProcess):
                process.kill()

        def kill_process() -> None:
            timer.expired = True  # type: ignore[attr-defined]
            process = psutil.Process(proc.pid)
            for child_process in process.children(recursive=True):
                do_kill_process(child_process)
            do_kill_process(process)

        assert testrun.stdout_filename is not None
        assert testrun.stderr_filename is not None
        with (
            open(testrun.stdout_filename, "w", encoding="utf-8") as stdout,
            open(testrun.stderr_filename, "w", encoding="utf-8") as stderr,
        ):
            testrun.record_lean_start_time()
            proc = subprocess.Popen(
                cmd, shell=True, cwd=testrun.solution.root_dir, stdout=stdout, stderr=stderr
            )

            timer = threading.Timer(timeout_sec, kill_process)
            timer.daemon = True
            timer.expired = False  # type: ignore[attr-defined]
            timer.start()
            proc.communicate()

            testrun.record_lean_end_time()
            if timer.expired:  # type: ignore[attr-defined]
                # Process killed by timer -> raise an exception.
                raise SubprocessTimeoutError(
                    message=f"Process #{proc.pid} killed after {timeout_sec} seconds",
                    timeout=timeout_sec,
                    exit_code=proc.returncode,
                )

            # Process completed naturally -> cancel the timer and return the exit code.
            timer.cancel()

            return proc.returncode
