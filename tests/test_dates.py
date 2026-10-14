from io import BytesIO, StringIO

import pytest

from cochange.cli import main
from cochange.dates import valid_date


@pytest.mark.parametrize(
    "value",
    [
        "0001-01-01",
        "0001-12-31",
        "0099-01-01",
        "1000-01-01",
        "1900-02-28",
        "2000-02-29",
        "2024-02-29",
        "2026-03-01",
        "9999-12-31",
    ],
)
def test_valid_date_accepts_real_calendar_dates_at_year_and_leap_boundaries(
    value: str,
) -> None:
    assert valid_date(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "0000-01-01",
        "0000-12-31",
        "2026-02-29",
        "1900-02-29",
        "2001-02-29",
        "2024-04-31",
        "2026-13-01",
        "2026-00-01",
        "2026-01-00",
        "2026-01-32",
        "2026-2-01",
        "2026-02-1",
        "2026/03/01",
        " 2026-03-01",
        "2026-03-01 ",
        "2026-03-01x",
        "2026-03-010",
        "2026-03-01-extra-date-value-000000000000000000",
        "٢٠٢٦-03-01",
        "2026-٠٣-01",
        "２０２６-03-01",
    ],
)
def test_valid_date_rejects_invalid_calendar_values_and_non_ascii_digits(
    value: str,
) -> None:
    assert not valid_date(value)


@pytest.mark.parametrize(
    ("option", "value", "diagnostic"),
    [
        (
            "--since",
            "2026-02-29",
            'invalid --since "2026-02-29" (expected a date as YYYY-MM-DD)',
        ),
        (
            "--since",
            "2026-03-01x",
            'invalid --since "2026-03-01x" (expected a date as YYYY-MM-DD)',
        ),
        (
            "--since",
            "٢٠٢٦-03-01",
            'invalid --since "????-03-01" (expected a date as YYYY-MM-DD)',
        ),
        (
            "--until",
            "0000-01-01",
            'invalid --until "0000-01-01" (expected a date as YYYY-MM-DD)',
        ),
        (
            "--until",
            "2026-03-01-extra-date-value-000000000000000000",
            ('invalid --until "2026-03-01-extra-date-value-000000000000000000" '
            "(expected a date as YYYY-MM-DD)"),
        ),
    ],
)
def test_cli_reports_exact_diagnostics_for_invalid_date_options(
    option: str, value: str, diagnostic: str
) -> None:
    stdout = StringIO()
    stderr = StringIO()

    result = main(["hot", option, value, "-"], BytesIO(), stdout, stderr)

    assert result == 2
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == f"cochange: {diagnostic}\n"


def test_cli_validates_since_before_until() -> None:
    stdout = StringIO()
    stderr = StringIO()

    result = main(
        ["hot", "--since", "2026-02-29", "--until", "2026-02-30", "-"],
        BytesIO(),
        stdout,
        stderr,
    )

    assert result == 2
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == (
        "cochange: invalid --since \"2026-02-29\" "
        "(expected a date as YYYY-MM-DD)\n"
    )


def test_cli_rejects_since_after_until_after_validating_both_dates() -> None:
    stdout = StringIO()
    stderr = StringIO()

    result = main(
        ["hot", "--since", "2026-03-02", "--until", "2026-03-01", "-"],
        BytesIO(),
        stdout,
        stderr,
    )

    assert result == 2
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == "cochange: --since is after --until\n"


def test_cli_date_range_includes_both_boundary_dates() -> None:
    history = b">abc1234\tAda\t2026-03-01\tfirst\n1\t0\tfile.py\n"
    stdout = StringIO()
    stderr = StringIO()

    result = main(
        ["hot", "--since", "2026-03-01", "--until", "2026-03-01", "-"],
        BytesIO(history),
        stdout,
        stderr,
    )

    assert result == 0
    assert stderr.getvalue() == ""
    assert "file.py" in stdout.getvalue()
    assert "\n" in stdout.getvalue()
    assert "\r" not in stdout.getvalue()


def test_cli_valid_date_range_with_no_matching_commits_returns_one() -> None:
    history = b">abc1234\tAda\t2026-03-01\tfirst\n1\t0\tfile.py\n"
    stdout = StringIO()
    stderr = StringIO()

    result = main(
        ["hot", "--since", "2026-03-02", "-"],
        BytesIO(history),
        stdout,
        stderr,
    )

    assert result == 1
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == "cochange: no commits in the selected range\n"
