import os
import subprocess

from hammurabi.grader.adapters.base import BaseSolutionAdapter


class CSharpSolutionAdapter(BaseSolutionAdapter):
    def __init__(self, solution):
        super().__init__(solution)

    @staticmethod
    def describe():
        subprocess.call("dotnet --version", shell=True)

    def get_language_name(self):
        return "csharp"

    def get_preferred_extensions(self):
        return [".cs"]

    def get_compile_command_line(self, testrun):
        # Create a temporary .csproj file for dotnet build
        project_name = testrun.solution.problem.name
        project_dir = testrun.solution.root_dir
        csproj_path = os.path.join(project_dir, f"{project_name}.csproj")

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
                f'    <Compile Include="{os.path.basename(file)}" />'
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
        with open(csproj_path, "w") as f:
            f.write(csproj_content)

        # Return the build command
        return f'cd "{project_dir}" && dotnet build "{csproj_path}" -c Release -o "{project_dir}"'

    def get_run_command_line(self, testrun):
        project_name = testrun.solution.problem.name
        dll_filename = os.path.join(testrun.solution.root_dir, f"{project_name}.dll")
        return ["dotnet", dll_filename]

    def _get_executable_filename(self, testrun):
        # For compatibility, though we now use DLLs
        return os.path.abspath(
            os.path.join(testrun.solution.root_dir, testrun.solution.problem.name + ".dll")
        )
