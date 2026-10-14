from collections.abc import Sequence
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from cochange.args import parse_args
from cochange.cli import main

USAGE = (
    "usage: cochange hot [--top N] [--since DATE] [--until DATE] LOG\n"
    "       cochange pairs [--top N] [--since DATE] [--until DATE] "
    "[--min-commits N] [--max-files N] LOG\n"
    "       cochange owners [--top N] [--since DATE] [--until DATE] "
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


@pytest.mark.parametrize(
    ("argv", "diagnostic"),
    [
        ([], "missing command (hot, pairs or owners)"),
        (["unknown"], 'unknown command "unknown"'),
        (["--help", "hot"], 'unknown command "--help"'),
        (["hot", "--help"], 'unknown option "--help"'),
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
