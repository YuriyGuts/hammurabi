class Problem(object):
    def __init__(self, name, root_dir, input_filename=None, output_filename=None,
                 solutions=None, testcases=None, reference_solution=None, config=None):
        self.name = name
        self.root_dir = root_dir
        self.input_filename = input_filename if input_filename is not None else name + ".in"
        self.output_filename = output_filename if output_filename is not None else name + ".out"
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
    def __init__(self, solution, testcase, output_dir, answer_filename, stdout_filename, stderr_filename,
                 result=None, score=None, memory_limit=None, time_limit=None):
        self.solution = solution
        self.testcase = testcase
        self.output_dir = output_dir
        self.answer_filename = answer_filename
        self.stdout_filename = stdout_filename
        self.stderr_filename = stderr_filename
        self.result = result
        self.score = score
        self.memory_limit = memory_limit
        self.time_limit = time_limit


class TestRunResult(object):
    def __init__(self, status_code, status):
        self.status_code = status_code
        self.status = status

    def __str__(self):
        return self.status


class TestRunCorrectResult(TestRunResult):
    def __init__(self):
        super(TestRunCorrectResult, self).__init__("C", "Correct")


class TestRunWrongResult(TestRunResult):
    def __init__(self):
        super(TestRunWrongResult, self).__init__("W", "Wrong")


class TestRunRuntimeErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunRuntimeErrorResult, self).__init__("R", "Runtime Error")
        self.message = message


class TestRunInternalErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunInternalErrorResult, self).__init__("X", "Internal Error")
        self.message = message


class TestRunCompilationErrorResult(TestRunResult):
    def __init__(self, message):
        super(TestRunCompilationErrorResult, self).__init__("E", "Compilation Error")
        self.message = message


class TestRunTimeoutResult(TestRunResult):
    def __init__(self):
        super(TestRunTimeoutResult, self).__init__("T", "Timeout")
