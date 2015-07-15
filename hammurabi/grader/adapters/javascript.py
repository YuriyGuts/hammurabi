from hammurabi.grader.adapters.base import BaseSolutionAdapter


class JavaScriptSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super(JavaScriptSolutionAdapter, self).__init__(solution)

    def get_run_command_line(self, testrun):
        entry_point_file = self.get_entry_point_file()
        return ["node", entry_point_file]
