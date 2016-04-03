import os
import subprocess
import hammurabi.utils.fileio as fileio

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import *
from hammurabi.utils.exceptions import *


class CppSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super(CppSolutionAdapter, self).__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("g++ --version", shell=True)

    def compile(self, testrun):
        cpp_sources = ' '.join(self._get_cpp_files())
        executable_filename = self._get_executable_filename(testrun)
        compile_cmd = "g++ -std=c++11 -O3 {cpp_sources} -o {executable_filename}".format(**locals())

        with open(testrun.compiler_output_filename, "w") as compiler_output_file:
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

    def get_run_command_line(self, testrun):
        executable_filename = self._get_executable_filename(testrun)
        return ["./" + executable_filename]

    def _get_cpp_files(self):
        return self.solution.get_files_by_predicate(lambda f: os.path.splitext(f)[1].lower() == ".cpp")

    def _get_executable_filename(self, testrun):
        return testrun.solution.problem.name
