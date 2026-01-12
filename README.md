# Hammurabi

_**Note**: This is a pet project I wrote about a decade ago. I’ve recently used it as a refactoring playground for agentic AI coding assistants, which turned out surprisingly well._

An automated judge for algorithmic programming contests. Strict, but fair.

Hammurabi discovers, compiles, and runs solutions in multiple programming languages. It detects compilation and runtime errors, validates output, enforces time limits, and generates HTML reports with detailed logs and statistics.

![Sample output from grader](/assets/grader-sample-output.png)

## Supported Languages

- C
- C++
- C#
- Java
- JavaScript (Node.js)
- Python
- Ruby

## Installation

Requires Python 3.10+. Install using [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Or install as a package:

```bash
uv pip install .
```

## Language Toolchain Setup

Hammurabi requires compilers and interpreters for each language you want to judge. Below are the recommended minimal installations for each platform.

### Quick Setup

#### Windows (using winget)

```cmd
winget install Microsoft.DotNet.SDK.9          # C#
winget install EclipseAdoptium.Temurin.21.JDK  # Java
winget install OpenJS.NodeJS.LTS               # JavaScript
winget install Python.Python.3.12              # Python
winget install RubyInstallerTeam.Ruby.3.3      # Ruby
```

For C/C++, choose one:
```cmd
# Option A: MinGW-w64 via MSYS2 (recommended, lighter)
# Download from https://www.msys2.org/, then:
pacman -S mingw-w64-ucrt-x86_64-gcc
# Add C:\msys64\ucrt64\bin to PATH

# Option B: Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive"
```

#### macOS (using Homebrew)

```bash
xcode-select --install  # C/C++ (clang)
brew install dotnet-sdk # C#
brew install openjdk    # Java
brew install node       # JavaScript
brew install python     # Python
brew install ruby       # Ruby
```

#### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install build-essential  # C/C++ (gcc/g++)
sudo apt install dotnet-sdk-9.0   # C#
sudo apt install default-jdk      # Java
sudo apt install nodejs npm       # JavaScript
sudo apt install python3          # Python
sudo apt install ruby             # Ruby
```

#### Linux (Fedora)

```bash
sudo dnf install gcc gcc-c++      # C/C++
sudo dnf install dotnet-sdk-9.0   # C#
sudo dnf install java-21-openjdk-devel  # Java
sudo dnf install nodejs npm       # JavaScript
sudo dnf install python3          # Python
sudo dnf install ruby             # Ruby
```

### Verify Installation

Run `hammurabi languages` to check which compilers/interpreters are detected:

```bash
hammurabi languages
```

## Usage

### Grading Solutions

```bash
hammurabi grade [OPTIONS]
```

Options:
- `--conf FILE` - Use an alternative config file (default: `hammurabi.yaml`)
- `--problem NAME [NAME ...]` - Grade only specific problems
- `--author NAME [NAME ...]` - Grade only specific authors' solutions
- `--reference` - Run only the reference solution (to generate correct answers)
- `--testcase NAME [NAME ...]` - Run only specific test cases

Examples:

```bash
# Grade all problems and solutions
hammurabi grade

# Grade a specific problem
hammurabi grade --problem fibonacci

# Grade a specific author's solutions
hammurabi grade --author alice

# Run the reference solution to generate expected outputs
hammurabi grade --reference
```

### Listing Language Support

```bash
hammurabi languages
```

Shows configured compilers and interpreters for each supported language.

## Directory Structure

Hammurabi expects problems to be organized in the following layout:

```
problems/
|-- problem_name/
|   |-- solutions/
|   |   |-- author1/
|   |   |   |-- solution.py
|   |   |-- author2/
|   |   |   |-- Solution.java
|   |   |-- _reference/
|   |   |   |-- solution.py
|   |-- testcases/
|   |   |-- 01.in
|   |   |-- 02.in
|   |-- answers/
|   |   |-- 01.out
|   |   |-- 02.out
|   |-- problem.yaml
```

- **solutions/**: Each subdirectory is an author's solution. The `_reference` author is special and used to generate expected outputs.
- **testcases/**: Input files with `.in` extension.
- **answers/**: Expected output files with `.out` extension, matching test case names.
- **problem.yaml**: Optional problem-specific configuration.

## Configuration

### hammurabi.yaml

The main configuration file. Place it in your project root directory. All relative paths are resolved from the directory containing this file.

```yaml
# Hammurabi grader configuration.
#
# Place this file in your project root. All relative paths below are resolved
# from the directory containing this file.

locations:
  # Directory containing your problem folders. Each subdirectory represents
  # one problem and should contain solutions/, testcases/, and answers/ folders.
  problem_root: problems

  # Directory where grading reports will be generated. A new timestamped
  # subfolder is created for each grading run.
  report_root: reports

  # Template for naming report subfolders. Available variables: {dt} for
  # datetime and {hostname} for the machine name.
  report_folder_template: "testrun-{dt:%Y%m%d-%H%M%S-%f}-{hostname}"

security:
  # Set to true to include the solution's standard output in reports.
  report_stdout: true

  # Set to true to include the solution's standard error in reports.
  report_stderr: true

runner:
  # The solution runner implementation to use.
  name: SubprocessSolutionRunner

  # Additional parameters passed to the runner.
  params: {}

# The default execution constraints applied to each problem.
# Can be overridden by problem-specific `problem.yaml` files.
limits:
  # Maximum memory allowed for each solution, in megabytes.
  memory: 512

  # The multiplier applied to all time limits.
  # Can be useful for running existing configurations
  # which were previously tested on faster/slower machines.
  time_limit_multiplier: 1.0

  # Maximum execution time per language, in seconds.
  time:
    c: 4.0
    cpp: 4.0
    csharp: 6.0
    java: 8.0
    javascript: 20.0
    php: 18.0
    python: 20.0
    ruby: 20.0

reporting:
  # Optional banners displayed at the top of HTML reports. Can include HTML.
  alert_banner: ""
  warning_banner: ""
  info_banner: ""
```

### problem.yaml

Optional problem-specific configuration. Place in each problem's directory to override settings from `hammurabi.yaml`.

```yaml
# Answer verification strategy.
# You can choose a built-in or a custom verifier.
verifier: IntegerSequenceVerifier

# Custom input/output filenames. Defaults to <problem_name>.in/.out.
problem_input_file: input.txt
problem_output_file: output.txt

# Score for each test case. Defaults to 1 point per test case.
testcase_score:
  "01": 10
  "02": 20
  "03": 30

# Override time limits for this problem.
limits:
  time:
    python: 30.0
```

### Custom Verifiers

Built-in verifiers:
- `AnswerVerifier` (strict byte-to-byte comparison)
- `IntegerSequenceVerifier`
- `FloatSequenceVerifier`
- `WordSequenceVerifier`

To create a custom verifier, add a Python file to `hammurabi/grader/verifiers/`. The verifier class must inherit from `AnswerVerifier`. See `custom.py` for an example template.

Then reference it in `problem.yaml`:

```yaml
verifier: FibonacciVerifier
```

## Development

Install dev dependencies:

```bash
uv sync
```

Available make targets:

```bash
make help          # Show all targets
make lint          # Run linter (check only)
make lint-fix      # Run linter with auto-fix
make format        # Format code
make typecheck     # Run type checker
make test          # Run tests
make check         # Run all checks
```

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.
