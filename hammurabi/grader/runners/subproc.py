import psutil
import subprocess
import threading

from hammurabi.grader.runners.base import BaseSolutionRunner
from hammurabi.grader.model import *
from hammurabi.utils.exceptions import *


class SubprocessSolutionRunner(BaseSolutionRunner):
    def __init__(self):
        super(SubprocessSolutionRunner, self).__init__()

    def run(self, testrun, cmd):
        config = testrun.solution.problem.config
        time_limit = config.get_safe("limits/time/{testrun.solution.language}".format(**locals()), default_value=20)
        multiplier = config.get_safe("limits/time_limit_multiplier", default_value=1.0)
        adjusted_time_limit = time_limit * multiplier

        try:
            self.run_command_with_timeout(testrun, cmd, adjusted_time_limit)
        except SubprocessTimeoutError as e:
            result = TestRunTimeoutResult(adjusted_time_limit)
            raise TestRunPrematureTerminationError(result)

    def run_command_with_timeout(self, testrun, cmd, timeout_sec):
        """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.

        Return subprocess exit code on natural completion of the subprocess.
        Raise an exception if timeout expires before subprocess completes."""

        def do_kill_process(process):
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass

        def kill_process():
            timer.expired = True
            process = psutil.Process(proc.pid)
            for child_process in process.children(recursive=True):
                do_kill_process(child_process)
            do_kill_process(process)

        with open(testrun.stdout_filename, "w") as stdout:
            with open(testrun.stderr_filename, "w") as stderr:
                testrun.record_lean_start_time()
                proc = subprocess.Popen(cmd, shell=True, cwd=testrun.solution.root_dir, stdout=stdout, stderr=stderr)

                timer = threading.Timer(timeout_sec, kill_process)
                timer.setDaemon(True)
                timer.expired = False
                timer.start()
                proc.communicate()

                testrun.record_lean_end_time()
                if timer.expired:
                    # Process killed by timer -> raise an exception.
                    raise SubprocessTimeoutError(
                        message="Process #{proc.pid} killed after {timeout_sec} seconds".format(**locals()),
                        timeout=timeout_sec,
                        exit_code=proc.returncode
                    )

                # Process completed naturally -> cancel the timer and return the exit code.
                timer.cancel()

                return proc.returncode
