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

    def compile(self, testrun):
        java_sources = ' '.join(self._get_java_files())
        compile_cmd = "javac -O -d . {java_sources}".format(**locals())

        with open(testrun.compiler_output_filename, "w") as compiler_output_file:
            exit_code = subprocess.call(
                compile_cmd,
                shell=True,
                cwd=self.solution.root_dir,
                stdout=compiler_output_file,
                stderr=compiler_output_file
            )

        if exit_code != 0:
            compiler_output = fileio.read_entire_file(testrun.compiler_output_filename)
            result = TestRunCompilationErrorResult(message=compiler_output)
            raise TestRunPrematureTerminationError(result)

        self.is_compiled = True

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        package_name = fileio.grep_value_from_file(entry_point_file, "package\s+([^\s;]+);", group_num=1)
        class_name = fileio.grep_value_from_file(entry_point_file, "class\s+(\w+)[^\w]+", group_num=1)

        if package_name is not None:
            class_name = "{package_name}.{class_name}".format(**locals())

        return ["java", class_name]

    def _get_java_files(self):
        return self.solution.get_files_by_predicate(lambda f: os.path.splitext(f)[1].lower() == ".java")
