import os
import platform
import subprocess
import hammurabi.utils.fileio as fileio

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import *
from hammurabi.utils.exceptions import *


class CSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super(CSolutionAdapter, self).__init__(solution)

    @staticmethod
    def describe():
        if platform.system() == "Windows":
            # Just use C++ compiler on Windows.
            subprocess.call("vsvars32.bat & cl", shell=True)
        else:
            subprocess.call("LC_ALL=C LANG=C gcc --version", shell=True)

    def get_language_name(self):
        return "c"

    def get_preferred_extensions(self):
        return [".c"]

    def get_compile_command_line(self, testrun):
        c_sources = ' '.join(['"{0}"'.format(file) for file in self.get_source_files()])
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            return "vsvars32.bat & cl /Ox /EHsc {c_sources} /link /out:\"{executable_filename}\"".format(**locals())
        else:
            # LANG=C forces gcc to use ASCII instead of UTF-8, so reports don't break when locale is set to UTF-8.
            return "LC_ALL=C LANG=C gcc --std=c99 -O2 {c_sources} -o \"{executable_filename}\"".format(**locals())

    def get_run_command_line(self, testrun):
        executable_filename = self._get_executable_filename(testrun)
        if platform.system() == "Windows":
            return [executable_filename]
        else:
            return ["./" + executable_filename]

    def _get_executable_filename(self, testrun):
        if platform.system() == "Windows":
            return os.path.abspath(os.path.join(testrun.solution.root_dir, testrun.solution.problem.name + ".exe"))
        else:
            return testrun.solution.problem.name
