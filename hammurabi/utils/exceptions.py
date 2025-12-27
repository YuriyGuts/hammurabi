class SubprocessTimeoutError(Exception):
    def __init__(self, message, timeout, exit_code):
        super().__init__(message)

        self.timeout = timeout
        self.exit_code = exit_code


class TestRunPrematureTerminationError(Exception):
    def __init__(self, testrun_result):
        super().__init__("Solution has failed before producing any answers.")

        self.result = testrun_result


class OutputDirectoryError(Exception):
    """Raised when the output directory cannot be created."""

    pass


class VerifierCreationError(Exception):
    """Raised when a verifier cannot be created."""

    pass
