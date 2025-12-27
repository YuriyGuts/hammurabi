"""C# solution adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path

from hammurabi.grader.adapters.base import BaseSolutionAdapter
from hammurabi.grader.model import Solution
from hammurabi.grader.model import TestRun


class CSharpSolutionAdapter(BaseSolutionAdapter):
    """Adapter for running C# solutions using .NET."""

    def __init__(self, solution: Solution | None) -> None:
        super().__init__(solution)

    @staticmethod
    def describe() -> None:
        subprocess.call("dotnet --version", shell=True)

    def get_language_name(self) -> str:
        return "csharp"

    def get_preferred_extensions(self) -> list[str]:
        return [".cs"]

    def get_compile_command_line(self, testrun: TestRun) -> str:
        # Create a temporary .csproj file for dotnet build
        project_name = testrun.solution.problem.name
        assert testrun.solution.root_dir is not None
        project_dir = Path(testrun.solution.root_dir)
        csproj_path = project_dir / f"{project_name}.csproj"

        # Detect available .NET version
        try:
            version_output = subprocess.check_output(
                ["dotnet", "--list-sdks"], universal_newlines=True
            )
            # Parse the first SDK version (format: "10.0.101 [/path/to/sdk]")
            first_sdk = version_output.strip().split("\n")[0]
            sdk_version = first_sdk.split()[0]
            major_version = sdk_version.split(".")[0]
            target_framework = f"net{major_version}.0"
        except Exception:
            # Fallback to net8.0 if detection fails
            target_framework = "net8.0"

        # Generate minimal .csproj content
        compile_includes = "\n".join(
            [
                f'    <Compile Include="{Path(file).name}" />'
                for file in self.get_source_files()
            ]
        )
        csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>{target_framework}</TargetFramework>
    <EnableDefaultItems>false</EnableDefaultItems>
    <AssemblyName>{project_name}</AssemblyName>
  </PropertyGroup>
  <ItemGroup>
{compile_includes}
  </ItemGroup>
</Project>"""

        # Write the .csproj file
        with open(csproj_path, "w", encoding="utf-8") as f:
            f.write(csproj_content)

        # Return the build command
        return f'cd "{project_dir}" && dotnet build "{csproj_path}" -c Release -o "{project_dir}"'

    def get_run_command_line(self, testrun: TestRun) -> list[str]:
        project_name = testrun.solution.problem.name
        assert testrun.solution.root_dir is not None
        dll_filename = Path(testrun.solution.root_dir) / f"{project_name}.dll"
        return ["dotnet", str(dll_filename)]

    def _get_executable_filename(self, testrun: TestRun) -> str:
        # For compatibility, though we now use DLLs
        assert testrun.solution.root_dir is not None
        dll_path = Path(testrun.solution.root_dir) / f"{testrun.solution.problem.name}.dll"
        return str(dll_path.resolve())
