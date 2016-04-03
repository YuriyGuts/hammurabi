import subprocess
from hammurabi.grader.adapters.base import BaseSolutionAdapter


class PythonSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super(PythonSolutionAdapter, self).__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("python --version", shell=True)

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        return ["python", entry_point_file]
