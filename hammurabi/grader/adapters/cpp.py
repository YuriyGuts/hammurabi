import os
import platform
import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter


class CppSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super().__init__(solution)

    @staticmethod
    def describe():
        if platform.system() == "Windows":
            subprocess.call("vsvars32.bat & cl", shell=True)
        else:
            subprocess.call("g++ --version", shell=True)

    def get_language_name(self):
        return "cpp"

    def get_preferred_extensions(self):
        return [".cpp"]

    def get_compile_command_line(self, testrun):
        cpp_sources = " ".join([f'"{file}"' for file in self.get_source_files()])
        executable_filename = self._get_executable_filename(testrun)

        if platform.system() == "Windows":
            return f'vsvars32.bat & cl /Ox /EHsc {cpp_sources} /link /out:"{executable_filename}"'
        else:
            return f'g++ -std=c++11 -O3 {cpp_sources} -o "{executable_filename}"'

    def get_run_command_line(self, testrun):
        executable_filename = self._get_executable_filename(testrun)
        if platform.system() == "Windows":
            return [executable_filename]
        else:
            return ["./" + executable_filename]

    def _get_executable_filename(self, testrun):
        if platform.system() == "Windows":
            return os.path.abspath(
                os.path.join(testrun.solution.root_dir, testrun.solution.problem.name + ".exe")
            )
        else:
            return testrun.solution.problem.name
