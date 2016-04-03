import subprocess
from hammurabi.grader.adapters.base import BaseSolutionAdapter


class RubySolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super(RubySolutionAdapter, self).__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("ruby --version", shell=True)

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        return ["ruby", entry_point_file]
