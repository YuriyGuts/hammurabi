class SubprocessTimeoutError(Exception):
    def __init__(self, message, timeout, exit_code):
        super(SubprocessTimeoutError, self).__init__(message)

        self.timeout = timeout
        self.exit_code = exit_code


class TestRunPrematureTerminationError(Exception):
    def __init__(self, testrun_result):
        super(TestRunPrematureTerminationError, self).__init__("Solution has failed before producing any answers.")

        self.result = testrun_result
