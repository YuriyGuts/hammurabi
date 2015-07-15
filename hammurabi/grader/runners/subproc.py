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

        try:
            self.run_command_with_timeout(testrun, cmd, time_limit)
        except SubprocessTimeoutError as e:
            result = TestRunTimeoutResult()
            raise TestRunPrematureTerminationError(result)

    def run_command_with_timeout(self, testrun, cmd, timeout_sec):
        """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.

        Return subprocess exit code on natural completion of the subprocess.
        Raise an exception if timeout expires before subprocess completes."""
        def kill_process():
            timer.expired = True
            proc.kill()

        with open(testrun.stdout_filename, "w") as stdout:
            with open(testrun.stderr_filename, "w") as stderr:
                proc = subprocess.Popen(cmd, shell=True, cwd=testrun.solution.root_dir, stdout=stdout, stderr=stderr)

                timer = threading.Timer(timeout_sec, kill_process)
                timer.expired = False
                timer.start()
                proc.communicate()

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
