import time
import traceback


class Problem(object):
    def __init__(self, name, root_dir, input_filename=None, output_filename=None,
                 solutions=None, testcases=None, reference_solution=None, config=None):
        self.name = name
        self.root_dir = root_dir
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.solutions = solutions if solutions is not None else []
        self.testcases = testcases if testcases is not None else []
        self.reference_solution = reference_solution
        self.config = config

    def __str__(self):
        return "Problem: {self.name}".format(**locals())


class Solution(object):
    def __init__(self, problem, author, root_dir, files=None, language=None, run_command=None):
        self.problem = problem
        self.author = author
        self.root_dir = root_dir
        self.files = files if files is not None else []
        self.language = language
        self.run_command = run_command

    def __str__(self):
        return "Problem: {self.problem.name}   Author: {self.author}   Language: {self.language}".format(**locals())

    def get_file_by_predicate(self, predicate):
        matches = self.get_files_by_predicate(predicate)
        return matches[0] if len(matches) > 0 else None

    def get_files_by_predicate(self, predicate):
        matches = [file for file in self.files if predicate(file)]
        return matches


class TestCase(object):
    def __init__(self, problem, name, input_filename, correct_answer_filename, score=1):
        self.problem = problem
        self.name = name
        self.input_filename = input_filename
        self.correct_answer_filename = correct_answer_filename
        self.score = score

    def __str__(self):
        return "Problem: {self.problem.name}   Filename: {self.input_filename}   Score: {self.score}".format(**locals())


class TestRun(object):
    def __init__(self, solution, testcase, output_dir, answer_filename, compiler_output_filename, stdout_filename, stderr_filename,
                 result=None, memory_limit=None, time_limit=None):
        self.solution = solution
        self.testcase = testcase
        self.output_dir = output_dir
        self.compiler_output_filename = compiler_output_filename
        self.answer_filename = answer_filename
        self.stdout_filename = stdout_filename
        self.stderr_filename = stderr_filename
        self.result = result
        self.judge_start_time = None
        self.judge_end_time = None
        self.lean_start_time = None
        self.lean_end_time = None
        self.memory_limit = memory_limit
        self.time_limit = time_limit
        self.data = {}

    def __str__(self):
        return "Solution: {self.solution.problem.name} / {self.solution.author}, Result: {self.result}".format(**locals())

    def record_judge_start_time(self):
        self.judge_start_time = self._get_timestamp()

    def record_judge_end_time(self):
        self.judge_end_time = self._get_timestamp()

    def record_lean_start_time(self):
        self.lean_start_time = self._get_timestamp()

    def record_lean_end_time(self):
        self.lean_end_time = self._get_timestamp()

    def get_judge_elapsed_milliseconds(self):
        return self.judge_end_time - self.judge_start_time

    def get_lean_elapsed_milliseconds(self):
        if self.lean_start_time is None or self.lean_end_time is None:
            return 0
        return self.lean_end_time - self.lean_start_time

    def _get_timestamp(self):
        return int(round(time.time() * 1000))


class TestRunResult(object):
    def __init__(self, status_code, status, score=0):
        self.status_code = status_code
        self.status = status
        self.score = score

    def __str__(self):
        return "[{self.status_code}] {self.status}, Score: {self.score}".format(**locals())

    def format_details(self):
        return None


class TestRunCorrectAnswerResult(TestRunResult):
    def __init__(self):
        super(TestRunCorrectAnswerResult, self).__init__("C", "Correct Answer")


class TestRunWrongAnswerResult(TestRunResult):
    def __init__(self, expected=None, actual=None, custom_message=None):
        super(TestRunWrongAnswerResult, self).__init__("W", "Wrong Answer")
        self.expected = expected
        self.actual = actual
        self.custom_message = custom_message

    def format_details(self):
        if self.custom_message is not None:
            return self.custom_message
        return "Expected: {self.expected}, Actual: {self.actual}".format(**locals())


class TestRunRuntimeErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunRuntimeErrorResult, self).__init__("R", "Runtime Error")
        self.message = message

    def format_details(self):
        return self.message


class TestRunFormatErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunFormatErrorResult, self).__init__("F", "Invalid Output Format")
        self.message = message

    def format_details(self):
        return self.message


class TestRunInternalErrorResult(TestRunResult):
    def __init__(self, exception):
        super(TestRunInternalErrorResult, self).__init__("X", "Judge Internal Error")
        self.exception = exception

    def format_details(self):
        if self.exception is None or len(self.exception) != 3:
            return super(TestRunInternalErrorResult, self).format_details()
        exc_type, exc, tb = self.exception
        return '\n'.join([str(exc_type), exc.message] + traceback.format_tb(tb))


class TestRunCompilationErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunCompilationErrorResult, self).__init__("E", "Compilation Error")
        self.message = message

    def format_details(self):
        return self.message


class TestRunSolutionMissingResult(TestRunResult):
    def __init__(self):
        super(TestRunSolutionMissingResult, self).__init__("M", "Solution Missing")


class TestRunUnverifiedResult(TestRunResult):
    def __init__(self, message):
        super(TestRunUnverifiedResult, self).__init__("U", "Unverified")
        self.message = message

    def format_details(self):
        return self.message


class TestRunTimeoutResult(TestRunResult):
    def __init__(self, timeout):
        super(TestRunTimeoutResult, self).__init__("T", "Timeout")
        self.timeout = timeout

    def format_details(self):
        return "Execution time exceeded the limit of {self.timeout:.2g} seconds".format(**locals())


class GraderJobScope(object):
    def __init__(self, tasks):
        self.tasks = tasks
