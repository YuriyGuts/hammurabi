# Hammurabi

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

## Usage

### Grading Solutions

```bash
hammurabi grade [OPTIONS]
```

Options:
- `--conf FILE` - Use an alternative config file (default: `grader.conf`)
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
|   |-- problem.conf
```

- **solutions/**: Each subdirectory is an author's solution. The `_reference` author is special and used to generate expected outputs.
- **testcases/**: Input files with `.in` extension.
- **answers/**: Expected output files with `.out` extension, matching test case names.
- **problem.conf**: Optional problem-specific configuration (JSON).

## Configuration

### grader.conf

Main configuration file (JSON) with all available options and their defaults:

```json
{
  "locations": {
    "problem_root": "grader/problems",
    "report_root": "grader/reports",
    "report_folder_template": "testrun-{dt:%Y%m%d-%H%M%S-%f}-{hostname}"
  },
  "limits": {
    "memory": 512,
    "time_limit_multiplier": 1.0,
    "time": {
      "c": 4.0,
      "cpp": 4.0,
      "csharp": 6.0,
      "java": 8.0,
      "javascript": 20.0,
      "php": 18.0,
      "python": 20.0,
      "ruby": 20.0
    }
  },
  "runner": {
    "name": "SubprocessSolutionRunner",
    "params": {}
  },
  "security": {
    "report_stdout": true,
    "report_stderr": true
  },
  "reporting": {
    "alert_banner": "",
    "warning_banner": "",
    "info_banner": ""
  }
}
```

#### Configuration Reference

| Section | Field | Description |
|---------|-------|-------------|
| `locations` | `problem_root` | Root directory containing problem folders |
| | `report_root` | Root directory for generated reports |
| | `report_folder_template` | Template for report folder names |
| `limits` | `memory` | Memory limit in MB |
| | `time_limit_multiplier` | Multiplier applied to all time limits |
| | `time.<language>` | Time limit in seconds per language |
| `runner` | `name` | Solution runner implementation |
| | `params` | Additional runner parameters |
| `security` | `report_stdout` | Include stdout in reports |
| | `report_stderr` | Include stderr in reports |
| `reporting` | `alert_banner` | Alert message shown in reports |
| | `warning_banner` | Warning message shown in reports |
| | `info_banner` | Info message shown in reports |

### problem.conf

Problem-specific configuration (JSON). All fields from `grader.conf` can be overridden, plus these additional fields:

```json
{
  "verifier": "IntegerSequenceVerifier",
  "problem_input_file": "input.txt",
  "problem_output_file": "output.txt",
  "testcase_score": {
    "01": 10,
    "02": 20,
    "03": 30
  },
  "limits": {
    "time": {
      "python": 30.0
    }
  }
}
```

#### Problem-Specific Fields

| Field | Description |
|-------|-------------|
| `verifier` | Answer verification strategy |
| `problem_input_file` | Custom input filename (default: `<problem_name>.in`) |
| `problem_output_file` | Custom output filename (default: `<problem_name>.out`) |
| `testcase_score` | Map of test case name to score (default: 1 point each) |

### Custom Verifiers

Built-in verifiers:
- `AnswerVerifier` (strict byte-to-byte comparison)
- `IntegerSequenceVerifier`
- `FloatSequenceVerifier`
- `WordSequenceVerifier`

To create a custom verifier, add a Python file to the `verifiers/` directory:

```
|-- verifiers/
    |-- common.py
    |-- fibonacci.py  <---
```

The verifier class must inherit from `AnswerVerifier`. Check `MyCustomVerifier` for an example implementation.

Then reference it in `problem.conf`:

```json
{
  "verifier": "FibonacciVerifier"
}
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
