import errno
import os
import shutil
import subprocess


class SolutionRunner(object):
    def __init__(self, config, solution):
        self.config = config
        self.solution = solution
        self.is_compiled = False
        self.output_dir = os.path.join(self.solution.root_dir, "output")

    def prepare(self):
        self.compile()
        self.clean_output()

    def clean_output(self):
        try:
            os.removedirs(self.output_dir)
        except:
            pass

        try:
            os.makedirs(self.output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise Exception("Internal error: cannot create output directory")

    def compile(self):
        self.is_compiled = True

    def get_entry_point_file(self):
        entry_point_file = None

        # If there's only one file, it must be the solution.
        if len(self.solution.files) == 1:
            entry_point_file = self.solution.files[0]

        # If there's more than one file, the file which has the name of the problem, must be the solution.
        if entry_point_file is None:
            entry_point_file = self.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower() == self.solution.problem.name.lower()
            )

        # If that fails, try to get the first file with the name 'main' or 'program'.
        if entry_point_file is None:
            entry_point_file = self.get_file_by_predicate(
                lambda f: os.path.splitext(os.path.basename(f))[0].lower() in ["main", "program"]
            )
        return entry_point_file

    def get_file_by_predicate(self, predicate):
        matches = [file for file in self.solution.files if predicate(file)]
        return matches[0] if len(matches) > 0 else None

    def supply_testcase(self, testcase):
        solution_input_filename = os.path.join(self.solution.root_dir, self.solution.problem.input_filename)
        shutil.copyfile(testcase.input_filename, solution_input_filename)

    def get_run_command_line(self, testcase):
        return [self.solution.language, self.get_entry_point_file()]

    def run(self, testcase):
        self.supply_testcase(testcase)
        cmd = ' '.join(self.get_run_command_line(testcase))
        subprocess.call(cmd, shell=True, cwd=self.solution.root_dir)
        self.collect_output(testcase)

    def collect_output(self, testcase):
        shutil.move(os.path.join(self.solution.root_dir, self.solution.problem.output_filename),
                    os.path.join(self.output_dir, os.path.basename(testcase.correct_answer_filename)))
