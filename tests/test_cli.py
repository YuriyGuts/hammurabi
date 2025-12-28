"""Tests for the CLI module."""

from __future__ import annotations

import sys
from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from hammurabi.cli import _describe_languages
from hammurabi.cli import _parse_command_line_args
from hammurabi.cli import _print_banner
from hammurabi.cli import _run_grader
from hammurabi.cli import main


class TestParseCommandLineArgs:
    """Tests for the _parse_command_line_args function."""

    def test_grade_command_basic(self):
        """Should parse basic grade command."""
        with patch.object(sys, "argv", ["hammurabi", "grade"]):
            args = _parse_command_line_args(["hammurabi", "grade"])

        assert args.command == "grade"
        assert args.conf is None
        assert args.problem is None
        assert args.author is None
        assert args.testcase is None
        assert args.reference is False

    def test_grade_command_with_conf(self):
        """Should parse --conf option."""
        with patch.object(sys, "argv", ["hammurabi", "grade", "--conf", "/path/to/conf"]):
            args = _parse_command_line_args(["hammurabi", "grade", "--conf", "/path/to/conf"])

        assert args.command == "grade"
        assert args.conf == "/path/to/conf"

    def test_grade_command_with_single_problem(self):
        """Should parse --problem with single value."""
        with patch.object(sys, "argv", ["hammurabi", "grade", "--problem", "problem1"]):
            args = _parse_command_line_args(["hammurabi", "grade", "--problem", "problem1"])

        assert args.problem == ["problem1"]

    def test_grade_command_with_multiple_problems(self):
        """Should parse --problem with multiple values."""
        argv = ["hammurabi", "grade", "--problem", "problem1", "problem2", "problem3"]
        with patch.object(sys, "argv", argv):
            args = _parse_command_line_args(argv)

        assert args.problem == ["problem1", "problem2", "problem3"]

    def test_grade_command_with_single_author(self):
        """Should parse --author with single value."""
        with patch.object(sys, "argv", ["hammurabi", "grade", "--author", "alice"]):
            args = _parse_command_line_args(["hammurabi", "grade", "--author", "alice"])

        assert args.author == ["alice"]

    def test_grade_command_with_multiple_authors(self):
        """Should parse --author with multiple values."""
        argv = ["hammurabi", "grade", "--author", "alice", "bob", "charlie"]
        with patch.object(sys, "argv", argv):
            args = _parse_command_line_args(argv)

        assert args.author == ["alice", "bob", "charlie"]

    def test_grade_command_with_reference_flag(self):
        """Should parse --reference flag."""
        with patch.object(sys, "argv", ["hammurabi", "grade", "--reference"]):
            args = _parse_command_line_args(["hammurabi", "grade", "--reference"])

        assert args.reference is True
        assert args.author is None

    def test_grade_command_author_and_reference_mutually_exclusive(self):
        """--author and --reference should be mutually exclusive."""
        argv = ["hammurabi", "grade", "--author", "alice", "--reference"]
        with patch.object(sys, "argv", argv), pytest.raises(SystemExit):
            _parse_command_line_args(argv)

    def test_grade_command_with_single_testcase(self):
        """Should parse --testcase with single value."""
        with patch.object(sys, "argv", ["hammurabi", "grade", "--testcase", "01"]):
            args = _parse_command_line_args(["hammurabi", "grade", "--testcase", "01"])

        assert args.testcase == ["01"]

    def test_grade_command_with_multiple_testcases(self):
        """Should parse --testcase with multiple values."""
        argv = ["hammurabi", "grade", "--testcase", "01", "02", "03"]
        with patch.object(sys, "argv", argv):
            args = _parse_command_line_args(argv)

        assert args.testcase == ["01", "02", "03"]

    def test_grade_command_with_all_options(self):
        """Should parse all options together."""
        argv = [
            "hammurabi",
            "grade",
            "--conf",
            "/path/to/conf",
            "--problem",
            "prob1",
            "prob2",
            "--author",
            "alice",
            "--testcase",
            "01",
            "02",
        ]
        with patch.object(sys, "argv", argv):
            args = _parse_command_line_args(argv)

        assert args.command == "grade"
        assert args.conf == "/path/to/conf"
        assert args.problem == ["prob1", "prob2"]
        assert args.author == ["alice"]
        assert args.testcase == ["01", "02"]

    def test_languages_command(self):
        """Should parse languages command."""
        with patch.object(sys, "argv", ["hammurabi", "languages"]):
            args = _parse_command_line_args(["hammurabi", "languages"])

        assert args.command == "languages"

    def test_no_command_returns_none(self):
        """Should return None for command when no command specified."""
        with patch.object(sys, "argv", ["hammurabi"]):
            args = _parse_command_line_args(["hammurabi"])

        assert args.command is None


class TestMain:
    """Tests for the main function."""

    @patch("hammurabi.cli._run_grader")
    @patch("hammurabi.cli._print_banner")
    @patch("hammurabi.cli._parse_command_line_args")
    def test_main_dispatches_to_grade(
        self, mock_parse: MagicMock, mock_banner: MagicMock, mock_run_grader: MagicMock
    ):
        """main() should dispatch to _run_grader for grade command."""
        mock_args = MagicMock()
        mock_args.command = "grade"
        mock_parse.return_value = mock_args

        main()

        mock_banner.assert_called_once()
        mock_run_grader.assert_called_once_with(mock_args)

    @patch("hammurabi.cli._describe_languages")
    @patch("hammurabi.cli._print_banner")
    @patch("hammurabi.cli._parse_command_line_args")
    def test_main_dispatches_to_languages(
        self,
        mock_parse: MagicMock,
        mock_banner: MagicMock,
        mock_describe: MagicMock,
    ):
        """main() should dispatch to _describe_languages for languages command."""
        mock_args = MagicMock()
        mock_args.command = "languages"
        mock_parse.return_value = mock_args

        main()

        mock_banner.assert_called_once()
        mock_describe.assert_called_once()

    @patch("hammurabi.cli._print_banner")
    @patch("hammurabi.cli._parse_command_line_args")
    def test_main_returns_none_for_unknown_command(
        self, mock_parse: MagicMock, mock_banner: MagicMock
    ):
        """main() should return None for unknown command."""
        mock_args = MagicMock()
        mock_args.command = "unknown"
        mock_parse.return_value = mock_args

        result = main()

        assert result is None

    @patch("hammurabi.cli._print_banner")
    @patch("hammurabi.cli._parse_command_line_args")
    def test_main_returns_none_for_no_command(self, mock_parse: MagicMock, mock_banner: MagicMock):
        """main() should return None when no command specified."""
        mock_args = MagicMock()
        mock_args.command = None
        mock_parse.return_value = mock_args

        result = main()

        assert result is None


class TestRunGrader:
    """Tests for the _run_grader function."""

    @patch("hammurabi.cli.grader.grade")
    def test_run_grader_calls_grader_grade(self, mock_grade: MagicMock):
        """_run_grader should call grader.grade with args."""
        mock_args = MagicMock()

        _run_grader(mock_args)

        mock_grade.assert_called_once_with(mock_args)


class TestDescribeLanguages:
    """Tests for the _describe_languages function."""

    @patch("hammurabi.cli.adapters.registered_adapters", {})
    def test_returns_zero_exit_code(self):
        """Should return 0 exit code."""
        result = _describe_languages()

        assert result == 0

    @patch("hammurabi.cli.adapters.registered_adapters")
    def test_prints_language_info(self, mock_adapters: MagicMock):
        """Should print information about each registered adapter."""
        mock_adapter = MagicMock()
        mock_adapter.__name__ = "MockAdapter"
        mock_adapters.items.return_value = [("python", mock_adapter)]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            _describe_languages()

        output = mock_stdout.getvalue()
        assert "python" in output
        assert "MockAdapter" in output

    @patch("hammurabi.cli.adapters.registered_adapters")
    def test_calls_describe_on_each_adapter(self, mock_adapters: MagicMock):
        """Should call describe() on each adapter."""
        mock_adapter1 = MagicMock()
        mock_adapter1.__name__ = "Adapter1"
        mock_adapter2 = MagicMock()
        mock_adapter2.__name__ = "Adapter2"
        mock_adapters.items.return_value = [
            ("lang1", mock_adapter1),
            ("lang2", mock_adapter2),
        ]

        _describe_languages()

        mock_adapter1.describe.assert_called_once()
        mock_adapter2.describe.assert_called_once()


class TestPrintBanner:
    """Tests for the _print_banner function."""

    @patch("hammurabi.cli.product.print_banner")
    def test_calls_product_print_banner(self, mock_print_banner: MagicMock):
        """Should call product.print_banner."""
        _print_banner()

        mock_print_banner.assert_called_once()


class TestErrorHandling:
    """Tests for error handling in CLI."""

    def test_invalid_argument_exits_with_error_code(self):
        """Invalid arguments should cause sys.exit with error code."""
        argv = ["hammurabi", "grade", "--invalid-option"]
        with (
            patch.object(sys, "argv", argv),
            pytest.raises(SystemExit) as exc_info,
        ):
            _parse_command_line_args(argv)

        assert exc_info.value.code != 0
