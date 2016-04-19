import codecs
import errno
import os
import shutil
import subprocess
import hammurabi.utils.fileio as fileio

from hammurabi.grader.model import *
from hammurabi.grader.runners import *
from hammurabi.utils.exceptions import *


class BaseSolutionAdapter(object):
    def __init__(self, solution):
        self.is_compiled = False
        self.solution = solution
        if solution is not None:
            self.config = solution.problem.config
            self.output_dir = os.path.join(self.config.report_output_dir, self.solution.problem.name, self.solution.author)

    @staticmethod
    def describe():
        pass

    def get_language_name(self):
        return None

    def get_preferred_extensions(self):
        return None

    def prepare(self):
        self.clean_output()

    def clean_output(self):
        try:
            os.removedirs(self.output_dir)
        except:
            pass

        try:
            os.makedirs(self.output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise Exception("Internal error: cannot create output directory")

    def compile(self, testrun):
        compile_cmd = self.get_compile_command_line(testrun)

        if compile_cmd is not None:
            with codecs.open(testrun.compiler_output_filename, "w", "utf-8") as compiler_output_file:
                exit_code = subprocess.call(
                    compile_cmd,
                    shell=True,
                    cwd=self.solution.root_dir,
                    stdout=compiler_output_file,
                    stderr=compiler_output_file
                )

            if exit_code != 0:
                compiler_output = fileio.read_entire_file(testrun.compiler_output_filename)
                result = TestRunCompilationErrorResult(message=compiler_output)
                raise TestRunPrematureTerminationError(result)

        self.is_compiled = True

    def get_compile_command_line(self, testrun):
        return None

    def get_entry_point_file(self):
        entry_point_file = None

        # If there's only one file, it must be the solution.
        if len(self.solution.files) == 1:
            entry_point_file = self.solution.files[0]

        # If there's more than one file, the file which has the name of the problem, must be the solution.
        if entry_point_file is None:
            entry_point_file = self.solution.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower() == self.solution.problem.name.lower()
            )

        # If that fails, try to get the first file with the name 'main' or 'program'.
        if entry_point_file is None:
            entry_point_file = self.solution.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower() in ["main", "program"]
            )
        return entry_point_file

    def supply_testcase(self, testcase):
        solution_input_filename = os.path.join(self.solution.root_dir, self.solution.problem.input_filename)
        shutil.copyfile(testcase.input_filename, solution_input_filename)

    def cleanup_testcase(self, testcase):
        solution_input_filename = os.path.join(self.solution.root_dir, self.solution.problem.input_filename)
        os.remove(solution_input_filename)

    def get_source_files(self):
        return self.solution.get_files_by_predicate(lambda f: os.path.splitext(f)[1].lower() in self.get_preferred_extensions())

    def get_run_command_line(self, testrun):
        return [self.solution.language, '"{0}"'.format(self.get_entry_point_file())]

    def get_run_command_line_string(self, testrun):
        return ' '.join(self.get_run_command_line(testrun))

    def create_testrun(self, testcase):
        compiler_output_filename = os.path.join(self.output_dir, "compiler_{testcase.name}.log".format(**locals()))
        answer_filename = os.path.join(self.output_dir, testcase.name + ".out")
        stdout_filename = os.path.join(self.output_dir, testcase.name + ".stdout")
        stderr_filename = os.path.join(self.output_dir, testcase.name + ".stderr")
        memory_limit = self.config.get_safe("limits/memory")
        time_limit = self.config.get_safe("limits/time/{self.solution.language}".format(**locals()))

        return TestRun(
            solution=self.solution,
            testcase=testcase,
            output_dir=self.output_dir,
            compiler_output_filename=compiler_output_filename,
            answer_filename=answer_filename,
            stdout_filename=stdout_filename,
            stderr_filename=stderr_filename,
            memory_limit=memory_limit,
            time_limit=self.config.get_safe("limits/time/{self.solution.language}".format(**locals()))
        )

    def run(self, testrun):
        if self.get_entry_point_file() is None:
            result = TestRunSolutionMissingResult()
            raise TestRunPrematureTerminationError(result)

        if not self.is_compiled:
            self.compile(testrun)

        try:
            self.supply_testcase(testrun.testcase)
            cmd = self.get_run_command_line_string(testrun)
            runner = self.create_runner(testrun, cmd)
            runner.run(testrun, cmd)
        finally:
            self.cleanup_testcase(testrun.testcase)

        self.collect_output(testrun)

    def create_runner(self, testrun, cmd):
        runner_class = testrun.solution.problem.config.get_safe("runner/name", default_value="SubprocessSolutionRunner")
        runner = globals()[runner_class]
        return runner()

    def collect_output(self, testrun):
        given_answer_filename = os.path.join(self.solution.root_dir, self.solution.problem.output_filename)
        if not os.path.exists(given_answer_filename):
            if os.path.getsize(testrun.stderr_filename) > 0:
                error_text = fileio.read_entire_file(testrun.stderr_filename)
                result = TestRunRuntimeErrorResult(message=error_text)
            else:
                msg = "Output file '{self.solution.problem.output_filename}' is empty or missing.".format(**locals())
                result = TestRunFormatErrorResult(msg)
            raise TestRunPrematureTerminationError(result)

        shutil.move(given_answer_filename, testrun.answer_filename)
