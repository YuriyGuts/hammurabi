"""Tests for the memory limiting module."""

from __future__ import annotations

import platform
import subprocess
import sys
import threading
from pathlib import Path
from unittest import mock

import pytest

from hammurabi.exceptions import SubprocessMemoryLimitError
from hammurabi.exceptions import TestRunPrematureTerminationError
from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunMemoryExceededResult
from hammurabi.grader.runners.memory import BaseMemoryLimiter
from hammurabi.grader.runners.memory import create_memory_limiter
from hammurabi.grader.runners.memory.fallback import PollingMemoryLimiter
from hammurabi.grader.runners.subproc import SubprocessSolutionRunner


@pytest.fixture
def sample_problem() -> Problem:
    """Create a sample problem for testing."""
    problem = Problem(name="test_problem", root_dir="/tmp/test")
    problem.config = ProblemConfig()
    return problem


@pytest.fixture
def sample_solution(sample_problem: Problem, tmp_path: Path) -> Solution:
    """Create a sample solution for testing."""
    return Solution(
        problem=sample_problem,
        author="test_author",
        root_dir=str(tmp_path),
        language="python",
    )


@pytest.fixture
def sample_testrun(sample_solution: Solution, tmp_path: Path) -> TestRun:
    """Create a sample test run for testing."""
    testcase = TestCase(
        problem=sample_solution.problem,
        name="01",
        input_filename=str(tmp_path / "input.in"),
        correct_answer_filename=str(tmp_path / "correct.out"),
        score=10,
    )

    return TestRun(
        solution=sample_solution,
        testcase=testcase,
        output_dir=str(tmp_path),
        answer_filename=str(tmp_path / "answer.out"),
        compiler_output_filename=None,
        stdout_filename=str(tmp_path / "stdout.txt"),
        stderr_filename=str(tmp_path / "stderr.txt"),
    )


class TestCreateMemoryLimiter:
    """Tests for the memory limiter factory function."""

    def test_returns_base_memory_limiter_instance(self):
        """Should return an instance that inherits from BaseMemoryLimiter."""
        limiter = create_memory_limiter(512)

        assert isinstance(limiter, BaseMemoryLimiter)

    def test_sets_memory_limit_mb(self):
        """Should set the memory limit in megabytes."""
        limiter = create_memory_limiter(256)

        assert limiter.memory_limit_mb == 256

    def test_sets_memory_limit_bytes(self):
        """Should convert memory limit to bytes."""
        limiter = create_memory_limiter(512)

        assert limiter.memory_limit_bytes == 512 * 1024 * 1024

    def test_creates_polling_limiter_on_macos(self, monkeypatch: pytest.MonkeyPatch):
        """Should create PollingMemoryLimiter on macOS."""
        monkeypatch.setattr(platform, "system", lambda: "Darwin")

        limiter = create_memory_limiter(512)

        assert isinstance(limiter, PollingMemoryLimiter)

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_creates_linux_limiter_on_linux(self, monkeypatch: pytest.MonkeyPatch):
        """Should create LinuxMemoryLimiter on Linux."""
        monkeypatch.setattr(platform, "system", lambda: "Linux")

        limiter = create_memory_limiter(512)

        from hammurabi.grader.runners.memory.linux import LinuxMemoryLimiter  # noqa: PLC0415

        assert isinstance(limiter, LinuxMemoryLimiter)

    def test_creates_windows_limiter_on_windows(self, monkeypatch: pytest.MonkeyPatch):
        """Should create WindowsMemoryLimiter on Windows."""
        monkeypatch.setattr(platform, "system", lambda: "Windows")

        limiter = create_memory_limiter(512)

        from hammurabi.grader.runners.memory.windows import WindowsMemoryLimiter  # noqa: PLC0415

        assert isinstance(limiter, WindowsMemoryLimiter)

    def test_creates_polling_limiter_on_unknown_platform(self, monkeypatch: pytest.MonkeyPatch):
        """Should fall back to PollingMemoryLimiter on unknown platforms."""
        monkeypatch.setattr(platform, "system", lambda: "UnknownOS")

        limiter = create_memory_limiter(512)

        assert isinstance(limiter, PollingMemoryLimiter)


class TestPollingMemoryLimiter:
    """Tests for the PollingMemoryLimiter class."""

    def test_get_preexec_fn_returns_none(self):
        """Polling limiter should not use preexec_fn."""
        limiter = PollingMemoryLimiter(512)

        assert limiter.get_preexec_fn() is None

    def test_attach_to_process_is_noop(self):
        """attach_to_process should be a no-op."""
        limiter = PollingMemoryLimiter(512)
        mock_proc = mock.MagicMock(spec=subprocess.Popen)

        # Should not raise
        limiter.attach_to_process(mock_proc)

    def test_stop_monitoring_without_start_is_safe(self):
        """stop_monitoring should be safe to call without start_monitoring."""
        limiter = PollingMemoryLimiter(512)

        # Should not raise
        limiter.stop_monitoring()

    def test_start_monitoring_tracks_peak_memory(self):
        """Should track peak memory usage during monitoring."""
        limiter = PollingMemoryLimiter(1024)  # 1GB limit
        callback_called = threading.Event()

        # Start a subprocess that uses some memory
        proc = subprocess.Popen(
            [sys.executable, "-c", "x = bytearray(1024 * 1024); import time; time.sleep(0.3)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        limiter.start_monitoring(proc, lambda: callback_called.set())

        # Wait for process to complete
        proc.wait()
        limiter.stop_monitoring()

        # Peak memory should have been recorded
        assert limiter.peak_memory_mb is not None
        assert limiter.peak_memory_mb > 0

    def test_start_monitoring_calls_callback_on_exceeded(self):
        """Should call callback when memory limit is exceeded."""
        limiter = PollingMemoryLimiter(1)  # 1 MB limit - very low
        callback_called = threading.Event()

        # Start a subprocess that allocates more than 1MB
        proc = subprocess.Popen(
            [sys.executable, "-c", "x = bytearray(10 * 1024 * 1024); import time; time.sleep(5)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        def on_exceeded():
            callback_called.set()
            proc.kill()

        limiter.start_monitoring(proc, on_exceeded)

        # Wait for callback or timeout
        callback_called.wait(timeout=2.0)
        limiter.stop_monitoring()
        proc.wait()

        assert callback_called.is_set(), "Memory exceeded callback was not called"

    def test_stop_monitoring_stops_thread(self):
        """stop_monitoring should stop the monitoring thread."""
        limiter = PollingMemoryLimiter(1024)

        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        limiter.start_monitoring(proc, lambda: None)

        # Monitoring thread should be running
        assert limiter._monitor_thread is not None
        assert limiter._monitor_thread.is_alive()

        limiter.stop_monitoring()
        proc.kill()
        proc.wait()

        # Thread should have stopped
        assert limiter._monitor_thread is None or not limiter._monitor_thread.is_alive()

    def test_get_peak_memory_mb_returns_tracked_value(self):
        """get_peak_memory_mb should return the tracked peak memory."""
        limiter = PollingMemoryLimiter(512)
        limiter.peak_memory_mb = 100

        assert limiter.get_peak_memory_mb() == 100

    def test_get_peak_memory_mb_returns_none_before_monitoring(self):
        """get_peak_memory_mb should return None if monitoring hasn't started."""
        limiter = PollingMemoryLimiter(512)

        assert limiter.get_peak_memory_mb() is None


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
class TestLinuxMemoryLimiter:
    """Tests for the LinuxMemoryLimiter class."""

    def test_get_preexec_fn_returns_callable(self):
        """Should return a callable function."""
        from hammurabi.grader.runners.memory.linux import LinuxMemoryLimiter  # noqa: PLC0415

        limiter = LinuxMemoryLimiter(512)
        preexec_fn = limiter.get_preexec_fn()

        assert callable(preexec_fn)

    def test_attach_to_process_is_noop(self):
        """attach_to_process should be a no-op on Linux."""
        from hammurabi.grader.runners.memory.linux import LinuxMemoryLimiter  # noqa: PLC0415

        limiter = LinuxMemoryLimiter(512)
        mock_proc = mock.MagicMock(spec=subprocess.Popen)

        # Should not raise
        limiter.attach_to_process(mock_proc)

    def test_start_monitoring_is_noop(self):
        """start_monitoring should be a no-op on Linux."""
        from hammurabi.grader.runners.memory.linux import LinuxMemoryLimiter  # noqa: PLC0415

        limiter = LinuxMemoryLimiter(512)
        mock_proc = mock.MagicMock(spec=subprocess.Popen)

        # Should not raise
        limiter.start_monitoring(mock_proc, lambda: None)

    def test_stop_monitoring_is_noop(self):
        """stop_monitoring should be a no-op on Linux."""
        from hammurabi.grader.runners.memory.linux import LinuxMemoryLimiter  # noqa: PLC0415

        limiter = LinuxMemoryLimiter(512)

        # Should not raise
        limiter.stop_monitoring()

    def test_preexec_fn_sets_rlimit(self):
        """preexec_fn should set RLIMIT_AS on Linux."""
        import resource  # noqa: PLC0415

        from hammurabi.grader.runners.memory.linux import LinuxMemoryLimiter  # noqa: PLC0415

        limiter = LinuxMemoryLimiter(512)
        preexec_fn = limiter.get_preexec_fn()

        # Call the preexec_fn
        preexec_fn()

        # Check that limit was set
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        expected = 512 * 1024 * 1024
        assert soft == expected
        assert hard == expected


class TestWindowsMemoryLimiter:
    """Tests for the WindowsMemoryLimiter class."""

    def test_inherits_from_polling_limiter(self):
        """Windows limiter should inherit from PollingMemoryLimiter."""
        from hammurabi.grader.runners.memory.windows import WindowsMemoryLimiter  # noqa: PLC0415

        limiter = WindowsMemoryLimiter(512)

        assert isinstance(limiter, PollingMemoryLimiter)

    def test_get_preexec_fn_returns_none(self):
        """Windows limiter should not use preexec_fn."""
        from hammurabi.grader.runners.memory.windows import WindowsMemoryLimiter  # noqa: PLC0415

        limiter = WindowsMemoryLimiter(512)

        assert limiter.get_preexec_fn() is None

    def test_stop_monitoring_is_safe(self):
        """stop_monitoring should be safe to call."""
        from hammurabi.grader.runners.memory.windows import WindowsMemoryLimiter  # noqa: PLC0415

        limiter = WindowsMemoryLimiter(512)

        # Should not raise
        limiter.stop_monitoring()


class TestMemoryLimitIntegration:
    """Integration tests for memory limiting with SubprocessSolutionRunner."""

    def test_runner_uses_memory_limit_from_testrun(self, sample_testrun: TestRun, tmp_path: Path):
        """Runner should use memory_limit from testrun."""
        runner = SubprocessSolutionRunner()
        sample_testrun.memory_limit = 512
        sample_testrun.solution.problem.config.limits.time.python = 5.0

        cmd = f"{sys.executable} -c \"print('ok')\""

        # Should not raise
        runner.run(sample_testrun, cmd)

    def test_runner_uses_default_memory_limit_when_none(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Runner should use default 512MB when memory_limit is None."""
        runner = SubprocessSolutionRunner()
        sample_testrun.memory_limit = None
        sample_testrun.solution.problem.config.limits.time.python = 5.0

        cmd = f"{sys.executable} -c \"print('ok')\""

        # Should not raise - uses default 512MB limit
        runner.run(sample_testrun, cmd)

    def test_memory_exceeded_raises_premature_termination(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Should raise TestRunPrematureTerminationError with memory exceeded result."""
        runner = SubprocessSolutionRunner()
        sample_testrun.memory_limit = 5  # 5MB - very low
        sample_testrun.solution.problem.config.limits.time.python = 10.0

        # Allocate more than 5MB
        cmd = f'{sys.executable} -c "x = bytearray(50 * 1024 * 1024); import time; time.sleep(5)"'

        with pytest.raises(TestRunPrematureTerminationError) as exc_info:
            runner.run(sample_testrun, cmd)

        assert isinstance(exc_info.value.result, TestRunMemoryExceededResult)
        assert exc_info.value.result.memory_limit_mb == 5

    def test_subprocess_memory_limit_error_contains_limit_info(self):
        """SubprocessMemoryLimitError should contain limit information."""
        error = SubprocessMemoryLimitError(
            message="Process exceeded memory limit",
            memory_limit_mb=512,
            peak_memory_mb=600,
        )

        assert error.memory_limit_mb == 512
        assert error.peak_memory_mb == 600
        assert "memory limit" in str(error)


class TestTestRunMemoryExceededResult:
    """Tests for the TestRunMemoryExceededResult model."""

    def test_status_code_is_m(self):
        """Status code should be 'M' for Memory limit exceeded."""
        result = TestRunMemoryExceededResult(memory_limit_mb=512)

        assert result.status_code == "M"

    def test_status_is_memory_limit_exceeded(self):
        """Status should be 'Memory Limit Exceeded'."""
        result = TestRunMemoryExceededResult(memory_limit_mb=512)

        assert result.status == "Memory Limit Exceeded"

    def test_format_details_without_peak(self):
        """format_details should work without peak memory."""
        result = TestRunMemoryExceededResult(memory_limit_mb=512)

        details = result.format_details()

        assert details is not None
        assert "512 MB" in details

    def test_format_details_with_peak(self):
        """format_details should include peak memory when available."""
        result = TestRunMemoryExceededResult(memory_limit_mb=512, peak_memory_mb=600)

        details = result.format_details()

        assert details is not None
        assert "600" in details
        assert "512" in details

    def test_is_not_correct(self):
        """Memory exceeded result should not be considered correct."""
        result = TestRunMemoryExceededResult(memory_limit_mb=512)

        assert not result.is_correct()

    def test_default_score_is_zero(self):
        """Default score should be zero."""
        result = TestRunMemoryExceededResult(memory_limit_mb=512)

        assert result.score == 0
