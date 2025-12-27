import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter


class PythonSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super().__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("python --version", shell=True)

    def get_language_name(self):
        return "python"

    def get_preferred_extensions(self):
        return [".py"]

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        return ["python", f'"{entry_point_file}"']
