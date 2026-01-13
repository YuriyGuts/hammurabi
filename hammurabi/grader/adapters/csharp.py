"""C# solution adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path

from jinja2 import Environment
from jinja2 import FileSystemLoader

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun

TEMPLATES_DIR = Path(__file__).parent.parent / "resources" / "templates"


class CSharpSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running C# solutions using .NET."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        """Print .NET SDK version information."""
        CSharpSolutionAdapter._run_version_command(["dotnet", "--version"])

    def get_language_name(self) -> str:
        """Return the language identifier."""
        return "csharp"

    def get_preferred_extensions(self) -> list[str]:
        """Return file extensions for C# source files."""
        return [".cs"]

    def get_compile_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to compile C# source files."""
        # Create a temporary .csproj file for dotnet build
        project_name = testrun.solution.problem.name
        assert testrun.solution.root_dir is not None
        project_dir = Path(testrun.solution.root_dir)
        csproj_path = project_dir / f"{project_name}.csproj"

        target_framework = self._detect_target_framework()
        source_files = [Path(f).name for f in self.get_source_files() if "obj" not in Path(f).parts]

        # Render .csproj from template
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template("csharp-project.csproj.jinja")
        csproj_content = template.render(
            project_name=project_name,
            target_framework=target_framework,
            source_files=source_files,
        )

        with open(csproj_path, "w", encoding="utf-8") as f:
            f.write(csproj_content)

        # Return the build command (cwd is set to solution.root_dir by the caller)
        return ["dotnet", "build", str(csproj_path), "-c", "Release", "-o", str(project_dir)]

    def _detect_target_framework(self) -> str:
        """Detect the installed .NET SDK version and return the target framework."""
        try:
            version_output = subprocess.check_output(
                ["dotnet", "--list-sdks"], universal_newlines=True, timeout=10
            )
            # Parse the first SDK version (format: "10.0.101 [/path/to/sdk]")
            first_sdk = version_output.strip().split("\n")[0]
            sdk_version = first_sdk.split()[0]
            major_version = sdk_version.split(".")[0]
            return f"net{major_version}.0"
        except Exception:
            # Fallback to net8.0 if detection fails
            return "net8.0"

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        """Return the command to execute the compiled .NET assembly."""
        project_name = testrun.solution.problem.name
        assert testrun.solution.root_dir is not None
        dll_filename = Path(testrun.solution.root_dir) / f"{project_name}.dll"
        return ["dotnet", str(dll_filename)]

    def _get_executable_filename(self, testrun: TestRun) -> str:
        # For compatibility, though we now use DLLs
        assert testrun.solution.root_dir is not None
        dll_path = Path(testrun.solution.root_dir) / f"{testrun.solution.problem.name}.dll"
        return str(dll_path.resolve())
