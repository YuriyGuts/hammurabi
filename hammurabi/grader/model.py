import time


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
                 result=None, start_time=None, memory_limit=None, time_limit=None):
        self.solution = solution
        self.testcase = testcase
        self.output_dir = output_dir
        self.compiler_output_filename = compiler_output_filename
        self.answer_filename = answer_filename
        self.stdout_filename = stdout_filename
        self.stderr_filename = stderr_filename
        self.result = result
        self.start_time = start_time
        self.end_time = None
        self.memory_limit = memory_limit
        self.time_limit = time_limit

    def __str__(self):
        return "Solution: {self.solution.problem.name} / {self.solution.author}, Result: {self.result}".format(**locals())

    def record_start_time(self):
        self.start_time = int(round(time.time() * 1000))

    def record_end_time(self):
        self.end_time = int(round(time.time() * 1000))

    def get_elapsed_milliseconds(self):
        return self.end_time - self.start_time


class TestRunResult(object):
    def __init__(self, status_code, status, score=None):
        self.status_code = status_code
        self.status = status
        self.score = score

    def __str__(self):
        return "[{self.status_code}] {self.status}, Score: {self.score}".format(**locals())


class TestRunCorrectAnswerResult(TestRunResult):
    def __init__(self):
        super(TestRunCorrectAnswerResult, self).__init__("C", "Correct Answer")


class TestRunWrongAnswerResult(TestRunResult):
    def __init__(self, expected=None, actual=None):
        super(TestRunWrongAnswerResult, self).__init__("W", "Wrong Answer")
        self.expected = expected
        self.actual = actual


class TestRunRuntimeErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunRuntimeErrorResult, self).__init__("R", "Runtime Error")
        self.message = message


class TestRunFormatErrorResult(TestRunResult):
    def __init__(self, exception=None):
        super(TestRunFormatErrorResult, self).__init__("F", "Invalid Output Format")
        self.exception = exception


class TestRunInternalErrorResult(TestRunResult):
    def __init__(self, exception):
        super(TestRunInternalErrorResult, self).__init__("X", "Judge Internal Error")
        self.exception = exception


class TestRunCompilationErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunCompilationErrorResult, self).__init__("E", "Compilation Error")
        self.message = message


class TestRunUnverifiedResult(TestRunResult):
    def __init__(self, message):
        super(TestRunUnverifiedResult, self).__init__("U", "Unverified")
        self.message = message


class TestRunTimeoutResult(TestRunResult):
    def __init__(self):
        super(TestRunTimeoutResult, self).__init__("T", "Timeout")


class GraderJobScope(object):
    def __init__(self, tasks):
        self.tasks = tasks
