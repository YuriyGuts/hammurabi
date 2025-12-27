import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter


class RubySolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super().__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("ruby --version", shell=True)

    def get_language_name(self):
        return "ruby"

    def get_preferred_extensions(self):
        return [".rb"]

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        return ["ruby", f'"{entry_point_file}"']
