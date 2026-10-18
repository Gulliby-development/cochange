from collections.abc import Sequence
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from cochange.args import parse_args
from cochange.cli import main

USAGE = (
    "usage: cochange hot [--top N] [--since DATE] [--until DATE] [--path DIR]... LOG\n"
    "       cochange pairs [--top N] [--since DATE] [--until DATE] [--path DIR]... "
    "[--min-commits N] [--max-files N] LOG\n"
    "       cochange owners [--top N] [--since DATE] [--until DATE] [--path DIR]... "
    "[--min-commits N] LOG\n"
)
HISTORY = b">abc1234\tAda\t2026-03-01\tfirst\n1\t0\tfile.py\n"


def _run(argv: Sequence[str], data: bytes = b"") -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    status = main(argv, BytesIO(data), stdout, stderr)
    return status, stdout.getvalue(), stderr.getvalue()


def _display(path: Path) -> str:
    return str(path).replace("\\", "/")


class _OrderedStringIO(StringIO):
    def __init__(self, name: str, events: list[str]) -> None:
        super().__init__()
        self.name = name
        self.events = events

    def write(self, value: str) -> int:
        if value:
            self.events.append(self.name)
        return super().write(value)


def _run_ordered(
    argv: Sequence[str], data: bytes
) -> tuple[int, str, str, list[str]]:
    events: list[str] = []
    stdout = _OrderedStringIO("stdout", events)
    stderr = _OrderedStringIO("stderr", events)
    status = main(argv, BytesIO(data), stdout, stderr)
    return status, stdout.getvalue(), stderr.getvalue(), events


def test_help_as_the_only_argument_prints_exact_usage() -> None:
    status, stdout, stderr = _run(["--help"])

    assert status == 0
    assert stdout == USAGE
    assert stderr == ""


@pytest.mark.parametrize("command", ["hot", "pairs", "owners"])
def test_help_after_command_prints_exact_usage(command: str) -> None:
    status, stdout, stderr = _run([command, "--help"])

    assert status == 0
    assert stdout == USAGE
    assert stderr == ""


def test_help_after_unknown_command_reports_unknown_command() -> None:
    status, stdout, stderr = _run(["frob", "--help"])

    assert status == 2
    assert stdout == ""
    assert stderr == 'cochange: unknown command "frob"\n'


@pytest.mark.parametrize(
    ("argv", "diagnostic"),
    [
        ([], "missing command (hot, pairs or owners)"),
        (["unknown"], 'unknown command "unknown"'),
        (["--help", "hot"], 'unknown command "--help"'),
        (["hot", "--help", "history.log"], 'unknown option "--help"'),
        (["owners", "--help=1"], 'unknown option "--help=1"'),
        (["pairs", "--other"], 'unknown option "--other"'),
        (["owners", "file.log", "--unknown"], 'unknown option "--unknown"'),
    ],
)
def test_command_and_unknown_option_errors_are_exact(
    argv: list[str], diagnostic: str
) -> None:
    status, stdout, stderr = _run(argv)

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {diagnostic}\n"


@pytest.mark.parametrize(
    ("command", "option"),
    [
        ("hot", "--top"),
        ("hot", "--since"),
        ("hot", "--until"),
        ("pairs", "--min-commits"),
        ("pairs", "--max-files"),
    ],
)
def test_last_option_without_a_value_has_the_exact_diagnostic(
    command: str, option: str
) -> None:
    status, stdout, stderr = _run([command, option])

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {option} needs a value\n"


def test_option_value_can_start_with_a_hyphen_and_is_validated_as_a_value() -> None:
    status, stdout, stderr = _run(["hot", "--top", "--unknown", "-"])

    assert status == 2
    assert stdout == ""
    assert stderr == (
        'cochange: invalid --top "--unknown" '
        "(expected a whole number from 1 to 1000)\n"
    )


def test_option_spellings_and_last_value_wins() -> None:
    parsed = parse_args(
        ["pairs", "--top", "1", "--top=2", "--min-commits=3", "--max-files", "4", "-"]
    )

    assert parsed.command == "pairs"
    assert parsed.top == 2
    assert parsed.min_commits == 3
    assert parsed.max_files == 4
    assert parsed.log == "-"


@pytest.mark.parametrize(
    ("command", "option", "value", "lower", "upper"),
    [
        ("hot", "--top", "0", 1, 1000),
        ("hot", "--top", "1001", 1, 1000),
        ("owners", "--min-commits", "0", 1, 100000),
        ("owners", "--min-commits", "100001", 1, 100000),
        ("pairs", "--min-commits", "0", 1, 100000),
        ("pairs", "--min-commits", "100001", 1, 100000),
        ("pairs", "--max-files", "1", 2, 1000),
        ("pairs", "--max-files", "1001", 2, 1000),
    ],
)
def test_numeric_options_reject_values_outside_their_bounds(
    command: str, option: str, value: str, lower: int, upper: int
) -> None:
    status, stdout, stderr = _run([command, f"{option}={value}", "-"])

    assert status == 2
    assert stdout == ""
    assert stderr == (
        f'cochange: invalid {option} "{value}" '
        f"(expected a whole number from {lower} to {upper})\n"
    )


@pytest.mark.parametrize(
    ("command", "option", "value"),
    [
        ("hot", "--top", "1"),
        ("hot", "--top", "1000"),
        ("owners", "--min-commits", "1"),
        ("owners", "--min-commits", "100000"),
        ("pairs", "--min-commits", "1"),
        ("pairs", "--min-commits", "100000"),
        ("pairs", "--max-files", "2"),
        ("pairs", "--max-files", "1000"),
    ],
)
def test_numeric_options_accept_both_inclusive_bounds(
    command: str, option: str, value: str
) -> None:
    status, stdout, stderr = _run([command, option, value, "-"])

    assert status == 2
    assert stdout == ""
    assert stderr == "cochange: <stdin>: no commits\n"


@pytest.mark.parametrize(
    ("command", "option", "value", "expected_range"),
    [
        ("hot", "--top", "+1", "1 to 1000"),
        ("hot", "--top", "-1", "1 to 1000"),
        ("hot", "--top", "01", "1 to 1000"),
        ("hot", "--top", "1.0", "1 to 1000"),
        ("hot", "--top", "١", "1 to 1000"),
        ("owners", "--min-commits", "01", "1 to 100000"),
        ("pairs", "--min-commits", "+2", "1 to 100000"),
        ("pairs", "--max-files", "01", "2 to 1000"),
        ("pairs", "--max-files", "2x", "2 to 1000"),
    ],
)
def test_numeric_options_reject_signs_leading_zeroes_and_non_digits(
    command: str, option: str, value: str, expected_range: str
) -> None:
    shown_value = "".join(char if "!" <= char <= "~" else "?" for char in value)
    status, stdout, stderr = _run([command, option, value, "-"])

    assert status == 2
    assert stdout == ""
    assert stderr == (
        f'cochange: invalid {option} "{shown_value}" '
        f"(expected a whole number from {expected_range})\n"
    )


@pytest.mark.parametrize(
    ("argv", "diagnostic"),
    [
        (
            ["hot", "--top=0", "--since=not-a-date", "-"],
            'invalid --top "0" (expected a whole number from 1 to 1000)',
        ),
        (
            ["hot", "--until=bad", "--since=2026-03-01x", "-"],
            'invalid --since "2026-03-01x" (expected a date as YYYY-MM-DD)',
        ),
        (
            ["hot", "--until=2026-03-010", "-"],
            'invalid --until "2026-03-010" (expected a date as YYYY-MM-DD)',
        ),
        (
            ["pairs", "--min-commits=0", "--max-files=1", "-"],
            ('invalid --min-commits "0" '
            "(expected a whole number from 1 to 100000)"),
        ),
        (
            ["pairs", "--max-files=1", "-"],
            'invalid --max-files "1" (expected a whole number from 2 to 1000)',
        ),
    ],
)
def test_option_values_are_validated_in_the_specified_order(
    argv: list[str], diagnostic: str
) -> None:
    status, stdout, stderr = _run(argv)

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {diagnostic}\n"


@pytest.mark.parametrize(
    ("argv", "diagnostic"),
    [
        (["hot", "--max-files=2", "-"], "--max-files is only valid for pairs"),
        (["hot", "--min-commits=1", "-"], "--min-commits is not valid for hot"),
        (
            ["hot", "--since=2026-03-02", "--until=2026-03-01", "-"],
            "--since is after --until",
        ),
        (["hot"], "missing LOG"),
        (["hot", "one.log", "two.log"], "too many arguments"),
    ],
)
def test_applicability_date_order_and_log_argument_errors(
    argv: list[str], diagnostic: str
) -> None:
    status, stdout, stderr = _run(argv)

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {diagnostic}\n"


def test_numeric_validation_precedes_option_applicability() -> None:
    status, stdout, stderr = _run(["hot", "--max-files=1", "-"])

    assert status == 2
    assert stdout == ""
    assert stderr == (
        'cochange: invalid --max-files "1" '
        "(expected a whole number from 2 to 1000)\n"
    )


def test_max_files_error_precedes_min_commits_error_for_hot() -> None:
    status, stdout, stderr = _run(
        ["hot", "--min-commits=1", "--max-files=2", "-"]
    )

    assert status == 2
    assert stdout == ""
    assert stderr == "cochange: --max-files is only valid for pairs\n"


def test_file_input_error_shows_the_supplied_path_with_forward_slashes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.log"
    status, stdout, stderr = _run(["hot", str(path)])

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {_display(path)}: cannot read the file\n"


def test_file_input_rejects_invalid_utf8_with_the_path(tmp_path: Path) -> None:
    path = tmp_path / "bad-utf8.log"
    path.write_bytes(b"\xff")
    status, stdout, stderr = _run(["hot", str(path)])

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {_display(path)}: input is not valid UTF-8\n"


def test_a_missing_path_in_backslash_form_is_displayed_with_forward_slashes(
    tmp_path: Path,
) -> None:
    path = str(tmp_path / "not-present.log").replace("/", "\\")
    status, stdout, stderr = _run(["hot", path])

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {path.replace(chr(92), '/')}: cannot read the file\n"


def test_empty_stdin_log_reports_the_stdin_display_name() -> None:
    status, stdout, stderr = _run(["hot", "-"])

    assert status == 2
    assert stdout == ""
    assert stderr == "cochange: <stdin>: no commits\n"


def test_log_parse_error_is_prefixed_with_log_name_and_line_number() -> None:
    malformed = b">abc1234\tAda\t2026-03-01\n"
    status, stdout, stderr = _run(["hot", "-"], malformed)

    assert status == 2
    assert stdout == ""
    assert stderr == (
        'cochange: <stdin>:1: expected ">HASH<TAB>AUTHOR<TAB>DATE<TAB>SUBJECT"\n'
    )


def test_no_commit_in_the_selected_range_exits_one_without_stdout() -> None:
    status, stdout, stderr = _run(
        ["hot", "--since=2026-03-02", "-"],
        HISTORY,
    )

    assert status == 1
    assert stdout == ""
    assert stderr == "cochange: no commits in the selected range\n"


def test_hot_command_reads_the_binary_stdin_and_prints_lf_terminated_report() -> None:
    status, stdout, stderr = _run(["hot", "-"], HISTORY)

    assert status == 0
    assert stdout == (
        "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
        "      1      1        0        1  2026-03-01  file.py\n"
    )
    assert stderr == ""
    assert "\r" not in stdout


PAIR_HISTORY = (
    b">abc1234\tAda\t2026-03-01\tfirst\n"
    b"1\t0\ta.py\n2\t1\tb.py\n"
    b">def5678\tBob\t2026-03-02\tsecond\n"
    b"3\t0\ta.py\n0\t2\tb.py\n"
)


def test_pairs_command_prints_successful_report_from_binary_stdin() -> None:
    status, stdout, stderr = _run(["pairs", "-", "--min-commits=1"], PAIR_HISTORY)

    assert status == 0
    assert stdout == (
        "TOGETHER    A->B    B->A  FILE A  FILE B\n"
        "       2  100.0%  100.0%  a.py    b.py\n"
    )
    assert stderr == ""


def test_owners_command_prints_successful_report_from_binary_stdin() -> None:
    status, stdout, stderr = _run(["owners", "-", "--min-commits=1"], PAIR_HISTORY)

    assert status == 0
    assert stdout == (
        "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"
        "      2        2  50.0%  Ada    a.py\n"
        "      2        2  50.0%  Ada    b.py\n"
        "2 files, 0 with a single author (0.0%)\n"
    )
    assert stderr == ""


def test_pairs_reports_singular_skipped_bulk_warning_after_the_table() -> None:
    history = PAIR_HISTORY + (
        b">1111111\tEve\t2026-03-03\tbulk\n"
        b"1\t0\ta.py\n1\t0\tb.py\n1\t0\tc.py\n"
    )

    status, stdout, stderr, events = _run_ordered(
        ["pairs", "--min-commits=1", "--max-files=2", "-"], history
    )

    assert status == 0
    assert stdout == (
        "TOGETHER    A->B    B->A  FILE A  FILE B\n"
        "       2  100.0%  100.0%  a.py    b.py\n"
    )
    assert stderr == "cochange: skipped 1 commit with more than 2 files\n"
    assert max(index for index, name in enumerate(events) if name == "stdout") < min(
        index for index, name in enumerate(events) if name == "stderr"
    )


def test_pairs_reports_plural_skipped_bulk_warning_after_header_only_table() -> None:
    history = (
        b">abc1234\tAda\t2026-03-01\tbulk one\n"
        b"1\t0\ta.py\n1\t0\tb.py\n1\t0\tc.py\n"
        b">def5678\tBob\t2026-03-02\tbulk two\n"
        b"1\t0\ta.py\n1\t0\tb.py\n1\t0\td.py\n"
    )

    status, stdout, stderr, events = _run_ordered(
        ["pairs", "--min-commits=1", "--max-files=2", "-"], history
    )

    assert status == 0
    assert stdout == "TOGETHER  A->B  B->A  FILE A  FILE B\n"
    assert stderr == "cochange: skipped 2 commits with more than 2 files\n"
    assert max(index for index, name in enumerate(events) if name == "stdout") < min(
        index for index, name in enumerate(events) if name == "stderr"
    )


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("hot", "COMMITS  ADDED  DELETED  AUTHORS  LAST  PATH\n"),
        ("pairs", "TOGETHER  A->B  B->A  FILE A  FILE B\n"),
        ("owners", "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"),
    ],
)
def test_merge_only_log_succeeds_with_header_only_output(command: str, expected: str) -> None:
    merge_only = b">abc1234\tAda\t2026-03-01\tmerge only\n"

    status, stdout, stderr = _run([command, "-"], merge_only)

    assert status == 0
    assert stdout == expected
    assert stderr == ""


PATH_HISTORY = (
    b">9a8b7c6\tDana\t2026-03-09\tRetry failed requests\n"
    b"2\t1\tsrc/client.py\n6\t0\ttests/test_client.py\n"
    b">8f7e6d5\tEli\t2026-03-05\tMerge branch 'config'\n"
    b">7e6d5c4\tEli\t2026-03-04\tLoad settings from TOML\n"
    b"10\t4\tsrc/config.py\n3\t3\tsrc/client.py\n1\t1\ttests/test_config.py\n"
    b">6d5c4b3\tDana\t2026-03-02\tMove helpers and add a logo\n"
    b"0\t0\tsrc/{util => helpers}/text.py\n-\t-\tdocs/logo.png\n"
    b"4\t2\tsrc/client.py\n"
    b">5c4b3a2\tSam\t2026-02-27\tReformat everything\n"
    b"8\t8\tsrc/client.py\n5\t5\tsrc/config.py\n"
    b"3\t3\ttests/test_client.py\n2\t2\ttests/test_config.py\n"
    b">4b3a291\tSam\t2026-02-20\tAdd the client\n"
    b"40\t0\tsrc/client.py\n15\t0\ttests/test_client.py\n"
)


def test_parse_args_collects_normalized_repeated_paths_and_keeps_scalar_options() -> None:
    parsed = parse_args(
      [
          "pairs",
          "--path",
          "src/",
          "--top",
          "3",
          "history.log",
          "--path=docs//",
          "--path",
          "-named",
      ]
    )

    assert parsed.paths == ("src", "docs", "-named")
    assert parsed.command == "pairs"
    assert parsed.top == 3
    assert parsed.log == "history.log"


def test_parse_args_defaults_to_no_paths_and_preserves_other_path_characters() -> None:
    assert parse_args(["hot", "-"]).paths == ()

    parsed = parse_args(
      ["hot", "--path=./src", "--path", "../src", "--path=src\\child", "-"]
    )

    assert parsed.paths == ("./src", "../src", "src\\child")


def test_parse_args_preserves_duplicate_and_overlapping_paths_in_order() -> None:
    parsed = parse_args(
      ["owners", "--path=src", "--path", "src", "--path=src/helpers", "-"]
    )

    assert parsed.paths == ("src", "src", "src/helpers")


def test_hot_path_filter_matches_the_supplied_exact_example() -> None:
    status, stdout, stderr = _run(
      ["hot", "--top", "3", "--path", "src", "-"], PATH_HISTORY
    )

    assert status == 0
    assert stdout == (
      "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
      "      5     57       14        3  2026-03-09  src/client.py\n"
      "      2     15        9        2  2026-03-04  src/config.py\n"
      "      1      0        0        1  2026-03-02  src/helpers/text.py\n"
    )
    assert stderr == ""
    assert "\r" not in stdout


def test_hot_path_union_includes_docs_in_the_specified_order() -> None:
    status, stdout, stderr = _run(
      ["hot", "--path", "src", "--path", "docs", "-"], PATH_HISTORY
    )

    assert status == 0
    assert stdout == (
      "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
      "      5     57       14        3  2026-03-09  src/client.py\n"
      "      2     15        9        2  2026-03-04  src/config.py\n"
      "      1      0        0        1  2026-03-02  docs/logo.png\n"
      "      1      0        0        1  2026-03-02  src/helpers/text.py\n"
    )
    assert stderr == ""


@pytest.mark.parametrize(
    ("argv", "expected_paths"),
    [
      (
            ["hot", "--path", "src/", "-"],
            ["src/client.py", "src/config.py", "src/helpers/text.py"],
        ),
        (
            ["hot", "--path=src//", "-"],
            ["src/client.py", "src/config.py", "src/helpers/text.py"],
        ),
        (["hot", "--path", "src/client.py", "-"], ["src/client.py"]),
    ],
)
def test_hot_path_spellings_trailing_slashes_and_exact_file(
    argv: list[str], expected_paths: list[str]
) -> None:
    status, stdout, stderr = _run(argv, PATH_HISTORY)

    assert status == 0
    rows = stdout.splitlines()[1:]
    assert [row.split()[-1] for row in rows] == expected_paths
    assert stderr == ""


def test_hot_top_is_applied_to_the_filtered_rows() -> None:
    status, stdout, stderr = _run(
      ["hot", "--path", "src", "--top", "1", "-"], PATH_HISTORY
    )

    assert status == 0
    assert stdout == (
      "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
      "      5     57       14        3  2026-03-09  src/client.py\n"
      "... 2 more files\n"
    )
    assert stderr == ""


def test_pairs_path_filter_matches_the_supplied_exact_example() -> None:
    status, stdout, stderr = _run(["pairs", "--path", "src", "-"], PATH_HISTORY)

    assert status == 0
    assert stdout == (
      "TOGETHER   A->B    B->A  FILE A         FILE B\n"
      "       2  40.0%  100.0%  src/client.py  src/config.py\n"
    )
    assert stderr == ""


def test_pairs_max_files_and_skipped_count_are_applied_after_path_filtering() -> None:
    status, stdout, stderr = _run(
      ["pairs", "--max-files", "2", "-"], PATH_HISTORY
    )

    assert status == 0
    assert stdout == (
      "TOGETHER    A->B    B->A  FILE A         FILE B\n"
      "       2  100.0%  100.0%  src/client.py  tests/test_client.py\n"
    )
    assert stderr == "cochange: skipped 3 commits with more than 2 files\n"

    filtered_status, filtered_stdout, filtered_stderr = _run(
      ["pairs", "--max-files", "2", "--path", "src", "-"], PATH_HISTORY
    )

    assert filtered_status == 0
    assert filtered_stdout == (
      "TOGETHER   A->B    B->A  FILE A         FILE B\n"
      "       2  40.0%  100.0%  src/client.py  src/config.py\n"
    )
    assert filtered_stderr == ""


def test_owners_path_filter_matches_the_supplied_exact_example() -> None:
    status, stdout, stderr = _run(
      ["owners", "--path", "tests", "--min-commits", "2", "-"], PATH_HISTORY
    )

    assert status == 0
    assert stdout == (
      "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"
      "      3        2  66.7%  Sam    tests/test_client.py\n"
      "      2        2  50.0%  Eli    tests/test_config.py\n"
      "2 files, 0 with a single author (0.0%)\n"
    )
    assert stderr == ""


@pytest.mark.parametrize(
    ("command", "header"),
    [
      ("hot", "COMMITS  ADDED  DELETED  AUTHORS  LAST  PATH\n"),
      ("pairs", "TOGETHER  A->B  B->A  FILE A  FILE B\n"),
      ("owners", "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"),
    ],
)
def test_filter_with_no_matching_files_keeps_selected_commits_and_prints_header(
    command: str, header: str
) -> None:
    status, stdout, stderr = _run([command, "--path", "nothing", "-"], PATH_HISTORY)

    assert status == 0
    assert stdout == header
    assert stderr == ""


@pytest.mark.parametrize(
    ("option", "value"),
    [
      ("--path", ""),
      ("--path", "/"),
      ("--path", "//"),
      ("--path=", ""),
      ("--path=", "/"),
      ("--path=", "//"),
    ],
)
def test_path_rejects_values_empty_after_trailing_slash_removal(
    option: str, value: str
) -> None:
    argv = ["hot", option, value, "-"] if option == "--path" else ["hot", f"{option}{value}", "-"]
    shown_value = value

    status, stdout, stderr = _run(argv, PATH_HISTORY)

    assert status == 2
    assert stdout == ""
    assert stderr == (
      f'cochange: invalid --path "{shown_value}" '
      "(expected a directory or file path)\n"
    )


def test_path_missing_value_and_invalid_repeated_value_have_exact_errors() -> None:
    missing_status, missing_stdout, missing_stderr = _run(["hot", "--path"], PATH_HISTORY)
    invalid_status, invalid_stdout, invalid_stderr = _run(
      ["hot", "--path=src", "--path", "/", "-"], PATH_HISTORY
    )

    assert missing_status == 2
    assert missing_stdout == ""
    assert missing_stderr == "cochange: --path needs a value\n"
    assert invalid_status == 2
    assert invalid_stdout == ""
    assert invalid_stderr == (
      'cochange: invalid --path "/" (expected a directory or file path)\n'
    )


@pytest.mark.parametrize(
    ("argv", "diagnostic"),
    [
      (
          ["hot", "--top=0", "--path=", "-"],
          'invalid --top "0" (expected a whole number from 1 to 1000)',
      ),
      (
          ["hot", "--path=", "--since=x", "-"],
          'invalid --since "x" (expected a date as YYYY-MM-DD)',
      ),
      (
          ["hot", "--until=x", "--path=", "-"],
          'invalid --until "x" (expected a date as YYYY-MM-DD)',
      ),
      (
          ["hot", "--path=", "--min-commits=0", "-"],
          'invalid --path "" (expected a directory or file path)',
      ),
      (
          ["pairs", "--min-commits=0", "--max-files=1", "--path=src", "-"],
          'invalid --min-commits "0" (expected a whole number from 1 to 100000)',
      ),
      (
          ["pairs", "--max-files=1", "--path=src", "-"],
          'invalid --max-files "1" (expected a whole number from 2 to 1000)',
      ),
    ],
)
def test_path_validation_preserves_the_required_error_precedence(
    argv: list[str], diagnostic: str
) -> None:
    status, stdout, stderr = _run(argv, PATH_HISTORY)

    assert status == 2
    assert stdout == ""
    assert stderr == f"cochange: {diagnostic}\n"


PATH_MATCH_HISTORY = (
    b">abc1234\tAda\t2026-03-01\tpaths\n"
    b"1\t0\tsrc\n"
    b"1\t0\tsrc/client.py\n"
    b"1\t0\tsrc2/a.py\n"
    b"1\t0\tSRC/a.py\n"
    b"1\t0\t./src/a.py\n"
    b"1\t0\t../src/a.py\n"
    b"1\t0\tsrc\\child.py\n"
    b"1\t0\tsrc/{util => helpers}/text.py\n"
)


def test_path_matching_uses_exact_equality_slash_boundaries_and_case() -> None:
    status, stdout, stderr = _run(["hot", "--path", "src", "-"], PATH_MATCH_HISTORY)

    assert status == 0
    assert {row.split()[-1] for row in stdout.splitlines()[1:]} == {
      "src",
      "src/client.py",
      "src/helpers/text.py",
    }
    assert stderr == ""


@pytest.mark.parametrize(
    ("directory", "matched"),
    [
      ("./src", "./src/a.py"),
      ("../src", "../src/a.py"),
      ("src\\child.py", "src\\child.py"),
      ("src/helpers/text.py", "src/helpers/text.py"),
    ],
)
def test_path_matching_preserves_literal_paths_and_matches_renames_by_destination(
    directory: str, matched: str
) -> None:
    status, stdout, stderr = _run(
      ["hot", "--path", directory, "-"], PATH_MATCH_HISTORY
    )

    assert status == 0
    assert [row.split()[-1] for row in stdout.splitlines()[1:]] == [matched]
    assert stderr == ""


def test_path_matching_does_not_match_a_rename_by_its_braced_source_form() -> None:
    status, stdout, stderr = _run(
      ["hot", "--path", "src/{util => helpers}", "-"], PATH_MATCH_HISTORY
    )

    assert status == 0
    assert stdout == (
      "COMMITS  ADDED  DELETED  AUTHORS  LAST  PATH\n"
    )
    assert stderr == ""


def test_duplicate_and_overlapping_filters_do_not_multiply_report_counts() -> None:
    single_status, single_stdout, single_stderr = _run(
      ["hot", "--path", "src", "-"], PATH_HISTORY
    )
    repeated_status, repeated_stdout, repeated_stderr = _run(
      ["hot", "--path", "src", "--path=src", "--path", "src/helpers", "-"],
      PATH_HISTORY,
    )

    assert single_status == repeated_status == 0
    assert repeated_stdout == single_stdout
    assert repeated_stderr == single_stderr == ""


def test_path_date_selection_precedes_filtering_and_top() -> None:
    status, stdout, stderr = _run(
      [
          "hot",
          "--since",
          "2026-03-09",
          "--until=2026-03-09",
          "--path",
          "src",
          "--top",
          "1",
          "-",
      ],
      PATH_HISTORY,
    )

    assert status == 0
    assert stdout == (
      "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
      "      1      2        1        1  2026-03-09  src/client.py\n"
    )
    assert stderr == ""

    empty_date_status, empty_date_stdout, empty_date_stderr = _run(
      ["hot", "--since=2026-03-10", "--path=src", "-"], PATH_HISTORY
    )

    assert empty_date_status == 1
    assert empty_date_stdout == ""
    assert empty_date_stderr == "cochange: no commits in the selected range\n"

    empty_files_status, empty_files_stdout, empty_files_stderr = _run(
      ["hot", "--since=2026-03-09", "--path=nothing", "-"], PATH_HISTORY
    )

    assert empty_files_status == 0
    assert empty_files_stdout == "COMMITS  ADDED  DELETED  AUTHORS  LAST  PATH\n"
    assert empty_files_stderr == ""


@pytest.mark.parametrize("directory", ["src/cli", "SRC", "src/util"])
def test_readme_history_nonmatching_paths_print_only_the_header(directory: str) -> None:
    status, stdout, stderr = _run(["hot", "--path", directory, "-"], PATH_HISTORY)

    assert status == 0
    assert stdout == "COMMITS  ADDED  DELETED  AUTHORS  LAST  PATH\n"
    assert stderr == ""
