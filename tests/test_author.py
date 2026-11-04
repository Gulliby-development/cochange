from collections.abc import Sequence
from io import BytesIO, StringIO

from cochange.cli import main

HISTORY = (
    b">abc1234\tDana\t2026-03-01\tfirst\n"
    b"1\t0\tsrc/shared.py\n"
    b"2\t0\tdocs/a.md\n"
    b">def5678\tEli\t2026-03-02\tsecond\n"
    b"3\t1\tsrc/shared.py\n"
    b"1\t0\tdocs/b.md\n"
    b">9876abc\tdana\t2026-03-03\tthird\n"
    b"4\t0\tsrc/shared.py\n"
    b"1\t0\tdocs/c.md\n"
    b">fedcba9\tDana\t2026-03-04\tfourth\n"
    b"5\t2\tsrc/shared.py\n"
    b"1\t0\tdocs/d.md\n"
)


def _run(argv: Sequence[str]) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    status = main(argv, BytesIO(HISTORY), stdout, stderr)
    return status, stdout.getvalue(), stderr.getvalue()


HOT_DANA = (
    "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
    "      2      6        2        1  2026-03-04  src/shared.py\n"
    "      1      2        0        1  2026-03-01  docs/a.md\n"
    "      1      1        0        1  2026-03-04  docs/d.md\n"
)
HOT_DANA_AND_ELI = (
    "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
    "      3      9        3        2  2026-03-04  src/shared.py\n"
    "      1      2        0        1  2026-03-01  docs/a.md\n"
    "      1      1        0        1  2026-03-02  docs/b.md\n"
    "      1      1        0        1  2026-03-04  docs/d.md\n"
)
HOT_DANA_LOWER = (
    "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
    "      1      4        0        1  2026-03-03  src/shared.py\n"
    "      1      1        0        1  2026-03-03  docs/c.md\n"
)
HOT_ALL = (
    "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
    "      4     13        3        3  2026-03-04  src/shared.py\n"
    "      1      2        0        1  2026-03-01  docs/a.md\n"
    "      1      1        0        1  2026-03-02  docs/b.md\n"
    "      1      1        0        1  2026-03-03  docs/c.md\n"
    "      1      1        0        1  2026-03-04  docs/d.md\n"
)
PAIRS_DANA = (
    "TOGETHER    A->B   B->A  FILE A     FILE B\n"
    "       1  100.0%  50.0%  docs/a.md  src/shared.py\n"
    "       1  100.0%  50.0%  docs/d.md  src/shared.py\n"
)
OWNERS_DANA = (
    "COMMITS  AUTHORS   SHARE  OWNER  PATH\n"
    "      2        1  100.0%  Dana   src/shared.py\n"
    "      1        1  100.0%  Dana   docs/a.md\n"
    "      1        1  100.0%  Dana   docs/d.md\n"
    "3 files, 3 with a single author (100.0%)\n"
)
PAIRS_DANA_LOWER = (
    "TOGETHER    A->B    B->A  FILE A     FILE B\n"
    "       1  100.0%  100.0%  docs/c.md  src/shared.py\n"
)
PAIRS_DANA_AND_ELI = (
    "TOGETHER    A->B   B->A  FILE A     FILE B\n"
    "       1  100.0%  33.3%  docs/a.md  src/shared.py\n"
    "       1  100.0%  33.3%  docs/b.md  src/shared.py\n"
    "       1  100.0%  33.3%  docs/d.md  src/shared.py\n"
)
PAIRS_ALL = (
    "TOGETHER    A->B   B->A  FILE A     FILE B\n"
    "       1  100.0%  25.0%  docs/a.md  src/shared.py\n"
    "       1  100.0%  25.0%  docs/b.md  src/shared.py\n"
    "       1  100.0%  25.0%  docs/c.md  src/shared.py\n"
    "       1  100.0%  25.0%  docs/d.md  src/shared.py\n"
)
OWNERS_DANA_LOWER = (
    "COMMITS  AUTHORS   SHARE  OWNER  PATH\n"
    "      1        1  100.0%  dana   docs/c.md\n"
    "      1        1  100.0%  dana   src/shared.py\n"
    "2 files, 2 with a single author (100.0%)\n"
)
OWNERS_DANA_AND_ELI = (
    "COMMITS  AUTHORS   SHARE  OWNER  PATH\n"
    "      3        2   66.7%  Dana   src/shared.py\n"
    "      1        1  100.0%  Dana   docs/a.md\n"
    "      1        1  100.0%  Eli    docs/b.md\n"
    "      1        1  100.0%  Dana   docs/d.md\n"
    "4 files, 3 with a single author (75.0%)\n"
)
OWNERS_ALL = (
    "COMMITS  AUTHORS   SHARE  OWNER  PATH\n"
    "      4        3   50.0%  Dana   src/shared.py\n"
    "      1        1  100.0%  Dana   docs/a.md\n"
    "      1        1  100.0%  Eli    docs/b.md\n"
    "      1        1  100.0%  dana   docs/c.md\n"
    "      1        1  100.0%  Dana   docs/d.md\n"
    "5 files, 4 with a single author (80.0%)\n"
)
HOT_DANA_SRC = (
    "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
    "      2      6        2        1  2026-03-04  src/shared.py\n"
)
HOT_COMMIT_FOUR = (
    "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH\n"
    "      1      5        2        1  2026-03-04  src/shared.py\n"
    "      1      1        0        1  2026-03-04  docs/d.md\n"
)
OWNERS_DANA_SRC = (
    "COMMITS  AUTHORS   SHARE  OWNER  PATH\n"
    "      2        1  100.0%  Dana   src/shared.py\n"
    "1 file, 1 with a single author (100.0%)\n"
)


def test_hot_author_selection_is_exact_repeatable_and_supports_equals_form() -> None:
    expected = (0, HOT_DANA, "")
    assert _run(["hot", "--author", "Dana", "-"]) == expected
    assert _run(["hot", "--author=Dana", "-"]) == expected

    assert _run(["hot", "--author", "dana", "-"]) == (0, HOT_DANA_LOWER, "")
    assert _run(["hot", "--author", "Dana", "--author", "Eli", "-"]) == (
        0,
        HOT_DANA_AND_ELI,
        "",
    )
    assert _run(["hot", "--author", "Nobody", "--author", "Dana", "-"]) == expected


def test_hot_without_author_keeps_all_commits() -> None:
    assert _run(["hot", "-"]) == (0, HOT_ALL, "")


def test_pairs_and_owners_accept_author_selection() -> None:
    pairs_dana = ["pairs", "--author", "Dana", "--min-commits", "1", "-"]
    owners_dana = ["owners", "--author", "Dana", "--min-commits", "1", "-"]
    assert _run(pairs_dana) == (0, PAIRS_DANA, "")
    assert _run(owners_dana) == (0, OWNERS_DANA, "")

    assert _run(["pairs", "--author", "dana", "--min-commits", "1", "-"]) == (
        0,
        PAIRS_DANA_LOWER,
        "",
    )
    assert _run(["owners", "--author", "dana", "--min-commits", "1", "-"]) == (
        0,
        OWNERS_DANA_LOWER,
        "",
    )

    pairs_repeat = [
        "pairs",
        "--author",
        "Dana",
        "--author",
        "Eli",
        "--min-commits",
        "1",
        "-",
    ]
    owners_repeat = [
        "owners",
        "--author",
        "Dana",
        "--author",
        "Eli",
        "--min-commits",
        "1",
        "-",
    ]
    assert _run(pairs_repeat) == (0, PAIRS_DANA_AND_ELI, "")
    assert _run(owners_repeat) == (0, OWNERS_DANA_AND_ELI, "")

    assert _run(["pairs", "--author=Dana", "--min-commits", "1", "-"]) == (
        0,
        PAIRS_DANA,
        "",
    )
    assert _run(["owners", "--author=Dana", "--min-commits", "1", "-"]) == (
        0,
        OWNERS_DANA,
        "",
    )
    assert _run(["pairs", "--author", "Nobody", "--author", "Dana", "--min-commits", "1", "-"]) == (
        0,
        PAIRS_DANA,
        "",
    )
    assert _run(
        ["owners", "--author", "Nobody", "--author", "Dana", "--min-commits", "1", "-"]
    ) == (0, OWNERS_DANA, "")

    assert _run(["pairs", "--min-commits", "1", "-"]) == (0, PAIRS_ALL, "")
    assert _run(["owners", "--min-commits", "1", "-"]) == (0, OWNERS_ALL, "")


def test_date_range_is_applied_before_author_selection() -> None:
    assert _run(
        ["hot", "--since", "2026-03-02", "--until", "2026-03-04", "--author", "Dana", "-"]
    ) == (0, HOT_COMMIT_FOUR, "")

    assert _run(
        ["owners", "--since", "2026-03-02", "--until", "2026-03-03", "--author", "Dana", "-"]
    ) == (1, "", "cochange: no commits by the selected authors\n")


def test_empty_date_selection_error_precedes_author_selection() -> None:
    assert _run(["pairs", "--since", "2026-04-01", "--author", "Nobody", "-"]) == (
        1,
        "",
        "cochange: no commits in the selected range\n",
    )
    assert _run(["pairs", "--author", "Nobody", "--min-commits", "1", "-"]) == (
        1,
        "",
        "cochange: no commits by the selected authors\n",
    )


def test_author_selection_precedes_path_filtering() -> None:
    assert _run(["hot", "--author", "Dana", "--path", "src", "-"]) == (
        0,
        HOT_DANA_SRC,
        "",
    )
    assert _run(["owners", "--author", "Dana", "--path", "src", "--min-commits", "1", "-"]) == (
        0,
        OWNERS_DANA_SRC,
        "",
    )

    assert _run(["hot", "--author", "Nobody", "-"]) == (
        1,
        "",
        "cochange: no commits by the selected authors\n",
    )
    assert _run(["hot", "--author", "Nobody", "--path", "absent", "-"]) == (
        1,
        "",
        "cochange: no commits by the selected authors\n",
    )


def test_empty_author_values_are_usage_errors() -> None:
    expected_error = (2, "", 'cochange: invalid --author "" (expected an author name)\n')
    cases = (
        ["hot", "--author", "", "-"],
        ["hot", "--author=", "-"],
    )
    for argv in cases:
        assert _run(argv) == expected_error


def test_path_validation_precedes_empty_author_and_minimum_validation() -> None:
    assert _run(["pairs", "--path", "", "--author", "", "--min-commits", "0", "-"]) == (
        2,
        "",
        'cochange: invalid --path "" (expected a directory or file path)\n',
    )
    assert _run(["pairs", "--author", "", "--min-commits", "0", "-"]) == (
        2,
        "",
        'cochange: invalid --author "" (expected an author name)\n',
    )
