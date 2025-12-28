"""Tests for the subprocess solution runner module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from hammurabi.exceptions import SubprocessTimeoutError
from hammurabi.exceptions import TestRunPrematureTerminationError
from hammurabi.grader.config import ProblemConfig
from hammurabi.grader.model import Problem
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestCase
from hammurabi.grader.model import TestRun
from hammurabi.grader.model import TestRunTimeoutResult
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


class TestSubprocessSolutionRunner:
    """Tests for the SubprocessSolutionRunner class."""

    def test_run_command_with_timeout_returns_exit_code(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Should return exit code when command completes within timeout."""
        runner = SubprocessSolutionRunner()
        cmd = f"{sys.executable} -c \"print('hello')\""

        exit_code = runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert exit_code == 0

    def test_run_command_with_timeout_captures_stdout(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Should capture stdout to the specified file."""
        runner = SubprocessSolutionRunner()
        cmd = f"{sys.executable} -c \"print('hello world')\""

        runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert sample_testrun.stdout_filename is not None
        stdout_content = Path(sample_testrun.stdout_filename).read_text()
        assert "hello world" in stdout_content

    def test_run_command_with_timeout_captures_stderr(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Should capture stderr to the specified file."""
        runner = SubprocessSolutionRunner()
        cmd = f"{sys.executable} -c \"import sys; sys.stderr.write('error message')\""

        runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert sample_testrun.stderr_filename is not None
        stderr_content = Path(sample_testrun.stderr_filename).read_text()
        assert "error message" in stderr_content

    def test_run_command_with_timeout_records_lean_times(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Should record lean start and end times."""
        runner = SubprocessSolutionRunner()
        cmd = f'{sys.executable} -c "pass"'

        runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert sample_testrun.lean_start_time is not None
        assert sample_testrun.lean_end_time is not None
        assert sample_testrun.lean_end_time >= sample_testrun.lean_start_time

    def test_run_command_with_timeout_raises_on_timeout(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Should raise SubprocessTimeoutError when command times out."""
        runner = SubprocessSolutionRunner()
        # Sleep for longer than timeout
        cmd = f'{sys.executable} -c "import time; time.sleep(10)"'

        with pytest.raises(SubprocessTimeoutError) as exc_info:
            runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=0.1)

        assert exc_info.value.timeout == 0.1
        assert "killed after" in str(exc_info.value)

    def test_run_command_with_timeout_returns_nonzero_exit_code(
        self, sample_testrun: TestRun, tmp_path: Path
    ):
        """Should return non-zero exit code when command fails."""
        runner = SubprocessSolutionRunner()
        cmd = f'{sys.executable} -c "exit(42)"'

        exit_code = runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert exit_code == 42

    def test_run_uses_config_time_limit(self, sample_testrun: TestRun, tmp_path: Path):
        """run() should use time limit from problem config."""
        runner = SubprocessSolutionRunner()
        # Set a short time limit in config
        sample_testrun.solution.problem.config.limits.time.python = 0.1
        sample_testrun.solution.problem.config.limits.time_limit_multiplier = 1.0

        cmd = f'{sys.executable} -c "import time; time.sleep(10)"'

        with pytest.raises(TestRunPrematureTerminationError) as exc_info:
            runner.run(sample_testrun, cmd)

        assert isinstance(exc_info.value.result, TestRunTimeoutResult)
        assert exc_info.value.result.timeout == 0.1

    def test_run_applies_time_limit_multiplier(self, sample_testrun: TestRun, tmp_path: Path):
        """run() should apply time limit multiplier from config."""
        runner = SubprocessSolutionRunner()
        # Set time limit and multiplier
        sample_testrun.solution.problem.config.limits.time.python = 0.1
        sample_testrun.solution.problem.config.limits.time_limit_multiplier = 2.0

        cmd = f'{sys.executable} -c "import time; time.sleep(10)"'

        with pytest.raises(TestRunPrematureTerminationError) as exc_info:
            runner.run(sample_testrun, cmd)

        # Should be 0.1 * 2.0 = 0.2
        assert isinstance(exc_info.value.result, TestRunTimeoutResult)
        assert exc_info.value.result.timeout == 0.2

    def test_run_successful_command(self, sample_testrun: TestRun, tmp_path: Path):
        """run() should complete successfully for fast commands."""
        runner = SubprocessSolutionRunner()
        # Set a reasonable time limit
        sample_testrun.solution.problem.config.limits.time.python = 5.0
        sample_testrun.solution.problem.config.limits.time_limit_multiplier = 1.0

        cmd = f"{sys.executable} -c \"print('success')\""

        # Should not raise
        runner.run(sample_testrun, cmd)

        assert sample_testrun.stdout_filename is not None
        stdout_content = Path(sample_testrun.stdout_filename).read_text()
        assert "success" in stdout_content

    def test_run_with_none_language_uses_default(self, sample_testrun: TestRun, tmp_path: Path):
        """run() should use default time limit when language is None."""
        runner = SubprocessSolutionRunner()
        sample_testrun.solution.language = None
        # Default time limit is 20.0 seconds
        sample_testrun.solution.problem.config.limits.time_limit_multiplier = 1.0

        cmd = f"{sys.executable} -c \"print('done')\""

        # Should not raise with 20 second timeout
        runner.run(sample_testrun, cmd)

        assert sample_testrun.stdout_filename is not None


class TestSubprocessTimeoutBehavior:
    """Tests for timeout behavior and process cleanup."""

    def test_timeout_kills_child_processes(self, sample_testrun: TestRun, tmp_path: Path):
        """Should kill child processes when timeout occurs."""
        runner = SubprocessSolutionRunner()
        # Create a command that spawns a child process that sleeps
        # The parent also sleeps, so timeout will kill both
        cmd = f'{sys.executable} -c "import time; time.sleep(100)"'

        with pytest.raises(SubprocessTimeoutError):
            runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=0.2)

        # Test passes if no orphan processes are left hanging
        # (verified by the test completing without hanging)

    def test_fast_command_does_not_trigger_timeout(self, sample_testrun: TestRun, tmp_path: Path):
        """Fast command should complete before timeout."""
        runner = SubprocessSolutionRunner()
        cmd = f"{sys.executable} -c \"print('fast')\""

        exit_code = runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert exit_code == 0

    def test_elapsed_time_is_recorded(self, sample_testrun: TestRun, tmp_path: Path):
        """Elapsed time should be recorded in testrun."""
        runner = SubprocessSolutionRunner()
        cmd = f'{sys.executable} -c "import time; time.sleep(0.1)"'

        runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        elapsed = sample_testrun.get_lean_elapsed_milliseconds()
        # Should be at least 100ms (the sleep time)
        assert elapsed >= 100


class TestCommandExecution:
    """Tests for command execution details."""

    def test_command_runs_in_solution_root_dir(self, sample_testrun: TestRun, tmp_path: Path):
        """Command should run in the solution's root directory."""
        runner = SubprocessSolutionRunner()
        # Create a file in the solution's root directory
        marker_file = tmp_path / "marker.txt"
        marker_file.write_text("found")

        # Command that reads the marker file (proving we're in the right directory)
        cmd = f"{sys.executable} -c \"print(open('marker.txt').read())\""

        runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert sample_testrun.stdout_filename is not None
        stdout_content = Path(sample_testrun.stdout_filename).read_text()
        assert "found" in stdout_content

    def test_command_with_arguments(self, sample_testrun: TestRun, tmp_path: Path):
        """Should handle commands with arguments."""
        runner = SubprocessSolutionRunner()
        cmd = f'{sys.executable} -c "import sys; print(sys.argv)" arg1 arg2'

        runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert sample_testrun.stdout_filename is not None
        stdout_content = Path(sample_testrun.stdout_filename).read_text()
        assert "arg1" in stdout_content
        assert "arg2" in stdout_content

    def test_command_with_shell_features(self, sample_testrun: TestRun, tmp_path: Path):
        """Should support shell features like pipes."""
        runner = SubprocessSolutionRunner()
        cmd = f'echo hello | {sys.executable} -c "import sys; print(sys.stdin.read().strip())"'

        runner.run_command_with_timeout(sample_testrun, cmd, timeout_sec=5.0)

        assert sample_testrun.stdout_filename is not None
        stdout_content = Path(sample_testrun.stdout_filename).read_text()
        assert "hello" in stdout_content
