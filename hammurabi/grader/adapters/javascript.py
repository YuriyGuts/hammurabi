import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter


class JavaScriptSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super().__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("node --version", shell=True)

    def get_language_name(self):
        return "javascript"

    def get_preferred_extensions(self):
        return [".js"]

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        return ["node", f'"{entry_point_file}"']
