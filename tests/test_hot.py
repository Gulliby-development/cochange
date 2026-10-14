from io import BytesIO, StringIO

from cochange.cli import main
from cochange.gitlog import parse_log
from cochange.hot import HotRow, analyze
from cochange.report import hot


def _commit(author: str, date: str, files: dict[str, tuple[int, int]]) -> dict[str, object]:
    return {"author": author, "date": date, "files": files}


def test_analyze_accepts_parsed_commit_objects() -> None:
    commits = parse_log(
        "<stdin>", ">abc1234\tAda\t2026-03-01\tfirst\n1\t0\tfile.py\n"
    )

    assert analyze(commits) == [HotRow(1, 1, 0, 1, "2026-03-01", "file.py")]


def _worked_example_commits() -> list[dict[str, object]]:
    return [
        _commit(
            "Dana",
            "2026-03-09",
            {"src/client.py": (2, 1), "tests/test_client.py": (6, 0)},
        ),
        _commit("Eli", "2026-03-05", {}),
        _commit(
            "Eli",
            "2026-03-04",
            {
                "src/config.py": (10, 4),
                "src/client.py": (3, 3),
                "tests/test_config.py": (1, 1),
            },
        ),
        _commit(
            "Dana",
            "2026-03-02",
            {
                "src/helpers/text.py": (0, 0),
                "docs/logo.png": (0, 0),
                "src/client.py": (4, 2),
            },
        ),
        _commit(
            "Sam",
            "2026-02-27",
            {
                "src/client.py": (8, 8),
                "src/config.py": (5, 5),
                "tests/test_client.py": (3, 3),
                "tests/test_config.py": (2, 2),
            },
        ),
        _commit(
            "Sam",
            "2026-02-20",
            {"src/client.py": (40, 0), "tests/test_client.py": (15, 0)},
        ),
    ]


def test_analyze_aggregates_each_touched_commit_exact_authors_and_latest_date() -> None:
    commits = [
        _commit("Dana", "2026-03-03", {"src/main.py": (2, 1), "image.png": (0, 0)}),
        _commit("Dana", "2026-03-01", {"src/main.py": (0, 4)}),
        _commit("dana", "2026-03-02", {"src/main.py": (1, 2)}),
        _commit("MergeBot", "2026-03-04", {}),
    ]

    assert analyze(commits) == [
        HotRow(3, 3, 7, 2, "2026-03-03", "src/main.py"),
        HotRow(1, 0, 0, 1, "2026-03-03", "image.png"),
    ]


def test_analyze_sorts_by_commit_count_then_changes_then_code_point_path() -> None:
    commits = [
        _commit(
            "A",
            "2026-03-01",
            {
                "z-hot.py": (0, 0),
                "c-changes.py": (4, 0),
                "B.py": (2, 0),
                "a.py": (1, 1),
            },
        ),
        _commit(
            "B",
            "2026-03-02",
            {
                "z-hot.py": (0, 0),
                "c-changes.py": (4, 0),
                "B.py": (1, 1),
                "a.py": (0, 2),
            },
        ),
        _commit("A", "2026-03-03", {"z-hot.py": (0, 0)}),
    ]

    assert [row.path for row in analyze(commits)] == [
        "z-hot.py",
        "c-changes.py",
        "B.py",
        "a.py",
    ]


def test_analyze_returns_no_rows_for_no_commits() -> None:
    assert analyze([]) == []


def test_supplied_hot_example_renders_exact_report_and_plural_more_notice() -> None:
    expected = """COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH
      5     57       14        3  2026-03-09  src/client.py
      3     24        3        2  2026-03-09  tests/test_client.py
      2     15        9        2  2026-03-04  src/config.py
... 3 more files"""

    assert hot(analyze(_worked_example_commits()), top=3) == expected


def test_hot_report_with_no_rows_is_header_only() -> None:
    assert hot([], top=10) == "COMMITS  ADDED  DELETED  AUTHORS  LAST  PATH"


def test_hot_report_uses_singular_notice_when_top_cuts_one_row() -> None:
    rows = [
        HotRow(2, 4, 1, 1, "2026-03-02", "a.py"),
        HotRow(1, 3, 2, 1, "2026-03-01", "b.py"),
    ]

    assert hot(rows, top=1) == (
        "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
        "      2      4        1        1  2026-03-02  a.py\n"
        "... 1 more file"
    )


def test_hot_report_does_not_add_notice_when_all_rows_fit() -> None:
    rows = [HotRow(1, 0, 0, 1, "2026-03-01", "file.py")]

    assert hot(rows, top=1) == (
        "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
        "      1      0        0        1  2026-03-01  file.py"
    )


def test_main_applies_inclusive_date_filter_before_hot_aggregation() -> None:
    log = (
        ">aaaaaaa\tOld\t2026-03-01\tbefore range\n"
        "9\t8\tsrc/a.py\n"
        ">bbbbbbb\tDana\t2026-03-02\tstart date\n"
        "2\t1\tsrc/a.py\n"
        ">ccccccc\tEli\t2026-03-03\tend date\n"
        "4\t0\tsrc/a.py\n"
        ">ddddddd\tNew\t2026-03-04\tafter range\n"
        "7\t6\tsrc/a.py\n"
    )
    stdout = StringIO()
    stderr = StringIO()

    status = main(
        ["hot", "--since", "2026-03-02", "--until=2026-03-03", "-"],
        stdin=BytesIO(log.encode("utf-8")),
        stdout=stdout,
        stderr=stderr,
    )

    assert status == 0
    assert stdout.getvalue() == (
        "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
        "      2      6        1        2  2026-03-03  src/a.py\n"
    )
    assert stderr.getvalue() == ""
