from cochange.owners import OwnerRow, analyze
from cochange.report import owners


def _commit(author: str, *paths: str) -> dict[str, object]:
    return {
        "author": author,
        "files": {path: (1, 0) for path in paths},
    }


def _worked_example_commits() -> list[dict[str, object]]:
    return [
        _commit("Dana", "src/client.py", "tests/test_client.py"),
        _commit("Eli"),
        _commit("Eli", "src/config.py", "src/client.py", "tests/test_config.py"),
        _commit("Dana", "src/helpers/text.py", "docs/logo.png", "src/client.py"),
        _commit("Sam", "src/client.py", "src/config.py", "tests/test_client.py", "tests/test_config.py"),
        _commit("Sam", "src/client.py", "tests/test_client.py"),
    ]


def test_analyze_counts_each_selected_commit_touching_a_path() -> None:
    commits = [
        _commit("Ada", "src/main.py", "image.png"),
        _commit("Ada", "src/main.py"),
        _commit("Grace", "src/main.py"),
        _commit("MergeBot"),
    ]

    assert analyze(commits, min_commits=1) == [
        OwnerRow(3, 2, 2, "Ada", "src/main.py"),
        OwnerRow(1, 1, 1, "Ada", "image.png"),
    ]


def test_analyze_counts_author_names_exactly() -> None:
    commits = [
        _commit("Ada", "src/main.py"),
        _commit("ada", "src/main.py"),
        _commit("Ada", "src/main.py"),
    ]

    assert analyze(commits, min_commits=1) == [
        OwnerRow(3, 2, 2, "Ada", "src/main.py"),
    ]


def test_analyze_breaks_owner_ties_by_code_point_name_order() -> None:
    commits = [
        _commit("ada", "src/main.py"),
        _commit("Ada", "src/main.py"),
        _commit("ada", "src/main.py"),
        _commit("Ada", "src/main.py"),
    ]

    assert analyze(commits, min_commits=1) == [
        OwnerRow(4, 2, 2, "Ada", "src/main.py"),
    ]


def test_analyze_uses_most_frequent_author_when_there_is_no_tie() -> None:
    commits = [
        _commit("Zoe", "src/main.py"),
        _commit("Ada", "src/main.py"),
        _commit("Zoe", "src/main.py"),
        _commit("Zoe", "src/main.py"),
    ]

    assert analyze(commits, min_commits=1) == [
        OwnerRow(4, 2, 3, "Zoe", "src/main.py"),
    ]


def test_analyze_default_minimum_is_three_commits() -> None:
    commits = [
        _commit("Ada", "two.py", "three.py"),
        _commit("Sam", "two.py", "three.py"),
        _commit("Dana", "three.py"),
    ]

    assert analyze(commits) == [OwnerRow(3, 3, 1, "Ada", "three.py")]


def test_analyze_includes_path_at_custom_minimum_boundary() -> None:
    commits = [
        _commit("Ada", "exact.py", "below.py"),
        _commit("Sam", "exact.py", "below.py"),
        _commit("Dana", "exact.py"),
    ]

    assert analyze(commits, min_commits=2) == [
        OwnerRow(3, 3, 1, "Ada", "exact.py"),
        OwnerRow(2, 2, 1, "Ada", "below.py"),
    ]


def test_analyze_omits_path_one_commit_below_custom_minimum() -> None:
    commits = [
        _commit("Ada", "exact.py", "below.py"),
        _commit("Sam", "exact.py"),
        _commit("Dana", "exact.py"),
    ]

    assert analyze(commits, min_commits=3) == [OwnerRow(3, 3, 1, "Ada", "exact.py")]


def test_analyze_sorts_by_commit_count_descending_then_path_code_point_order() -> None:
    commits = [
        _commit("Ada", "B.py", "a.py", "é.py", "low.py"),
        _commit("Sam", "B.py", "a.py", "é.py", "low.py"),
        _commit("Dana", "B.py", "a.py", "é.py", "z.py"),
        _commit("Dana", "z.py"),
        _commit("Sam", "z.py"),
        _commit("Ada", "z.py"),
    ]

    assert analyze(commits) == [
        OwnerRow(4, 3, 2, "Dana", "z.py"),
        OwnerRow(3, 3, 1, "Ada", "B.py"),
        OwnerRow(3, 3, 1, "Ada", "a.py"),
        OwnerRow(3, 3, 1, "Ada", "é.py"),
    ]


def test_analyze_returns_no_rows_without_commits() -> None:
    assert analyze([]) == []


def test_analyze_returns_no_rows_for_commits_without_files() -> None:
    assert analyze([_commit("MergeBot"), _commit("Ada")]) == []


def test_supplied_owners_example_matches_exact_report() -> None:
    assert owners(analyze(_worked_example_commits())) == (
        "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"
        "      5        3  40.0%  Dana   src/client.py\n"
        "      3        2  66.7%  Sam    tests/test_client.py\n"
        "2 files, 0 with a single author (0.0%)"
    )


def test_owner_report_with_no_rows_is_header_only() -> None:
    assert owners([], top=10) == "COMMITS  AUTHORS  SHARE  OWNER  PATH"


def test_owner_report_single_author_summary_uses_singular_file_label() -> None:
    rows = [OwnerRow(2, 1, 2, "Ada", "only.py")]

    assert owners(rows) == (
        "COMMITS  AUTHORS   SHARE  OWNER  PATH\n"
        "      2        1  100.0%  Ada    only.py\n"
        "1 file, 1 with a single author (100.0%)"
    )


def test_owner_report_summary_uses_plural_file_label_and_half_up_percent() -> None:
    rows = [
        OwnerRow(3, 1, 3, "Ada", "a.py"),
        OwnerRow(2, 2, 1, "Sam", "b.py"),
    ]

    assert owners(rows) == (
        "COMMITS  AUTHORS   SHARE  OWNER  PATH\n"
        "      3        1  100.0%  Ada    a.py\n"
        "      2        2   50.0%  Sam    b.py\n"
        "2 files, 1 with a single author (50.0%)"
    )


def test_owner_report_share_rounds_half_up_for_six_point_two_five_percent() -> None:
    rows = [OwnerRow(16, 2, 1, "Ada", "rare.py")]

    assert owners(rows) == (
        "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"
        "     16        2   6.3%  Ada    rare.py\n"
        "1 file, 0 with a single author (0.0%)"
    )


def test_owner_report_summary_counts_all_qualifying_rows_after_top_cut() -> None:
    rows = [
        OwnerRow(5, 3, 3, "Dana", "src/a.py"),
        OwnerRow(3, 1, 3, "Sam", "src/b.py"),
        OwnerRow(2, 2, 1, "Lee", "src/c.py"),
    ]

    assert owners(rows, top=1) == (
        "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"
        "      5        3  60.0%  Dana   src/a.py\n"
        "3 files, 1 with a single author (33.3%)\n"
        "... 2 more files"
    )


def test_owner_report_uses_singular_more_notice_when_one_row_is_cut() -> None:
    rows = [
        OwnerRow(3, 2, 2, "Ada", "a.py"),
        OwnerRow(2, 1, 2, "Sam", "b.py"),
    ]

    assert owners(rows, top=1) == (
        "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"
        "      3        2  66.7%  Ada    a.py\n"
        "2 files, 1 with a single author (50.0%)\n"
        "... 1 more file"
    )


def test_owner_report_has_no_more_notice_when_all_rows_fit() -> None:
    rows = [OwnerRow(2, 1, 1, "Ada", "a.py")]

    assert owners(rows, top=1) == (
        "COMMITS  AUTHORS  SHARE  OWNER  PATH\n"
        "      2        1  50.0%  Ada    a.py\n"
        "1 file, 1 with a single author (100.0%)"
    )
