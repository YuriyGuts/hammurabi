import errno
import os
import shutil
import subprocess
from hammurabi.grader.model import *


class BaseSolutionAdapter(object):
    def __init__(self, solution, config):
        self.solution = solution
        self.config = config
        self.is_compiled = False
        self.output_dir = os.path.join(self.config.report_output_dir, self.solution.author)

    def prepare(self):
        self.compile()
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

    def compile(self):
        self.is_compiled = True

    def get_entry_point_file(self):
        entry_point_file = None

        # If there's only one file, it must be the solution.
        if len(self.solution.files) == 1:
            entry_point_file = self.solution.files[0]

        # If there's more than one file, the file which has the name of the problem, must be the solution.
        if entry_point_file is None:
            entry_point_file = self.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower() == self.solution.problem.name.lower()
            )

        # If that fails, try to get the first file with the name 'main' or 'program'.
        if entry_point_file is None:
            entry_point_file = self.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower() in ["main", "program"]
            )
        return entry_point_file

    def get_file_by_predicate(self, predicate):
        matches = [file for file in self.solution.files if predicate(file)]
        return matches[0] if len(matches) > 0 else None

    def supply_testcase(self, testcase):
        solution_input_filename = os.path.join(self.solution.root_dir, self.solution.problem.input_filename)
        shutil.copyfile(testcase.input_filename, solution_input_filename)

    def get_run_command_line(self, testcase):
        return [self.solution.language, self.get_entry_point_file()]

    def get_run_command_line_string(self, testcase):
        return ' '.join(self.get_run_command_line(testcase))

    def create_testrun(self, testcase):
        answer_filename = os.path.join(self.output_dir, testcase.name + ".out")
        stdout_filename = os.path.join(self.output_dir, testcase.name + ".stdout")
        stderr_filename = os.path.join(self.output_dir, testcase.name + ".stderr")
        memory_limit = self.config.get_safe("limits/memory")
        time_limit = self.config.get_safe("limits/time/{self.solution.language}".format(**locals()))

        return TestRun(solution=self.solution,
                       testcase=testcase,
                       output_dir=self.output_dir,
                       answer_filename=answer_filename,
                       stdout_filename=stdout_filename,
                       stderr_filename=stderr_filename,
                       memory_limit=memory_limit,
                       time_limit=self.config.get_safe("limits/time/{self.solution.language}".format(**locals())))

    def run(self, testcase):
        testrun = self.create_testrun(testcase)

        self.supply_testcase(testcase)
        cmd = self.get_run_command_line_string(testcase)

        with open(testrun.stdout_filename, "w") as stdout:
            with open(testrun.stderr_filename, "w") as stderr:
                subprocess.call(cmd, shell=True, cwd=self.solution.root_dir, stdout=stdout, stderr=stderr)

        self.collect_output(testrun)

        return testrun

    def collect_output(self, testrun):
        shutil.move(os.path.join(self.solution.root_dir, self.solution.problem.output_filename),
                    testrun.answer_filename)
