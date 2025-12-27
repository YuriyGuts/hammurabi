import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.utils import fileio


class JavaSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super().__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("java -version", shell=True)
        subprocess.call("javac -version", shell=True)

    def get_language_name(self):
        return "java"

    def get_preferred_extensions(self):
        return [".java"]

    def get_compile_command_line(self, testrun):
        java_sources = " ".join([f'"{file}"' for file in self.get_source_files()])
        return f"javac -O -d . {java_sources}"

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        package_name = fileio.grep_value_from_file(
            entry_point_file, r"package\s+([^\s;]+);", group_num=1
        )
        class_name = fileio.grep_value_from_file(
            entry_point_file, r"class\s+(\w+)[^\w]+", group_num=1
        )

        if package_name is not None:
            class_name = f"{package_name}.{class_name}"

        return ["java", class_name]
