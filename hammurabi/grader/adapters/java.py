import os
import subprocess
import hammurabi.utils.fileio as fileio

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import *
from hammurabi.utils.exceptions import *


class JavaSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super(JavaSolutionAdapter, self).__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("java -version", shell=True)
        subprocess.call("javac -version", shell=True)

    def get_language_name(self):
        return "java"

    def get_preferred_extensions(self):
        return [".java"]

    def get_compile_command_line(self, testrun):
        java_sources = ' '.join(['"{0}"'.format(file) for file in self.get_source_files()])
        return "javac -O -d . {java_sources}".format(**locals())

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        package_name = fileio.grep_value_from_file(entry_point_file, "package\s+([^\s;]+);", group_num=1)
        class_name = fileio.grep_value_from_file(entry_point_file, "class\s+(\w+)[^\w]+", group_num=1)

        if package_name is not None:
            class_name = "{package_name}.{class_name}".format(**locals())

        return ["java", class_name]
