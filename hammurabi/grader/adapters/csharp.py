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

    def get_language_name(self):
        return "csharp"

    def get_preferred_extensions(self):
        return [".cs"]

    def get_compile_command_line(self, testrun):
        csharp_sources = ' '.join(['"{0}"'.format(file) for file in self.get_source_files()])
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            return "vsvars32.bat & csc /o+ {csharp_sources} /out:\"{executable_filename}\"".format(**locals())
        else:
            return "mcs -r:Mono.Security -optimize+ {csharp_sources} -out:{executable_filename}".format(**locals())

    def get_run_command_line(self, testrun):
        executable_filename = self._get_executable_filename(testrun)
        if platform.system() == "Windows":
            return [executable_filename]
        else:
            return ["mono", executable_filename]

    def _get_executable_filename(self, testrun):
        return os.path.abspath(os.path.join(testrun.solution.root_dir, testrun.solution.problem.name + ".exe"))
