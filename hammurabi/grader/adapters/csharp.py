import os
import platform
import subprocess
import hammurabi.utils.fileio as fileio

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import *
from hammurabi.utils.exceptions import *


class CSharpSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super(CSharpSolutionAdapter, self).__init__(solution)

    @staticmethod
    def describe():
        if platform.system() == "Windows":
            subprocess.call("vsvars32.bat & csc", shell=True)
        else:
            subprocess.call("mono --version", shell=True)
            subprocess.call("mcs --version", shell=True)

    def compile(self, testrun):
        csharp_sources = ' '.join(['"{0}"'.format(file) for file in self._get_csharp_files()])
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            compile_cmd = "vsvars32.bat & csc /o+ {csharp_sources} /out:\"{executable_filename}\"".format(**locals())
        else:
            compile_cmd = "mcs -r:Mono.Security -optimize+ {csharp_sources} -out:{executable_filename}".format(**locals())

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
        if platform.system() == "Windows":
            return [executable_filename]
        else:
            return ["mono", executable_filename]

    def _get_csharp_files(self):
        return self.solution.get_files_by_predicate(lambda f: os.path.splitext(f)[1].lower() == ".cs")

    def _get_executable_filename(self, testrun):
        if platform.system() == "Windows":
            return os.path.abspath(os.path.join(testrun.solution.root_dir, testrun.solution.problem.name + ".exe"))
        else:
            return testrun.solution.problem.name
