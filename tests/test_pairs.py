from cochange.pairs import PairRow, analyze
from cochange.report import pairs


def _commit(files: dict[str, tuple[int, int]]) -> dict[str, object]:
    return {"files": files}


def _worked_example_commits() -> list[dict[str, object]]:
    return [
        _commit({"src/client.py": (2, 1), "tests/test_client.py": (6, 0)}),
        _commit({}),
        _commit(
            {
                "src/config.py": (10, 4),
                "src/client.py": (3, 3),
                "tests/test_config.py": (1, 1),
            }
        ),
        _commit(
            {
                "src/helpers/text.py": (0, 0),
                "docs/logo.png": (0, 0),
                "src/client.py": (4, 2),
            }
        ),
        _commit(
            {
                "src/client.py": (8, 8),
                "src/config.py": (5, 5),
                "tests/test_client.py": (3, 3),
                "tests/test_config.py": (2, 2),
            }
        ),
        _commit({"src/client.py": (40, 0), "tests/test_client.py": (15, 0)}),
    ]


def test_analyze_counts_pairs_and_each_paths_eligible_commit_denominator() -> None:
    rows, skipped = analyze(
        [
            _commit({"a.py": (1, 0), "b.py": (0, 1), "c.py": (0, 0)}),
            _commit({"a.py": (2, 0), "b.py": (0, 2)}),
            _commit({"a.py": (3, 0), "c.py": (0, 3)}),
            _commit({"a.py": (4, 0)}),
        ],
        min_commits=1,
    )

    assert rows == [
        PairRow(2, 2, 4, 2, 2, "a.py", "b.py"),
        PairRow(2, 2, 4, 2, 2, "a.py", "c.py"),
        PairRow(1, 1, 2, 1, 2, "b.py", "c.py"),
    ]
    assert skipped == 0


def test_analyze_includes_exact_max_files_boundary_and_skips_only_larger_commits() -> None:
    rows, skipped = analyze(
        [
            _commit({"a.py": (0, 0), "b.py": (0, 0), "c.py": (0, 0)}),
            _commit({"a.py": (0, 0), "b.py": (0, 0)}),
            _commit(
                {
                    "a.py": (0, 0),
                    "b.py": (0, 0),
                    "x.py": (0, 0),
                    "y.py": (0, 0),
                }
            ),
        ],
        min_commits=1,
        max_files=3,
    )

    assert rows == [
        PairRow(2, 2, 2, 2, 2, "a.py", "b.py"),
        PairRow(1, 1, 2, 1, 1, "a.py", "c.py"),
        PairRow(1, 1, 2, 1, 1, "b.py", "c.py"),
    ]
    assert skipped == 1


def test_analyze_empty_and_single_file_commits_produce_no_pairs_or_skips() -> None:
    assert analyze([_commit({}), _commit({"only.py": (0, 0)})]) == ([], 0)


def test_analyze_min_commits_includes_the_threshold_and_excludes_lower_counts() -> None:
    rows, skipped = analyze(
        [
            _commit({"a.py": (0, 0), "b.py": (0, 0), "c.py": (0, 0)}),
            _commit({"a.py": (0, 0), "b.py": (0, 0)}),
            _commit({"a.py": (0, 0)}),
        ],
        min_commits=2,
    )

    assert rows == [PairRow(2, 2, 3, 2, 2, "a.py", "b.py")]
    assert skipped == 0


def test_analyze_defaults_to_two_commits_per_reported_pair() -> None:
    assert analyze([_commit({"a.py": (0, 0), "b.py": (0, 0)})]) == ([], 0)


def test_analyze_sorts_by_together_count_then_both_code_point_paths() -> None:
    rows, skipped = analyze(
        [
            _commit({"z.py": (0, 0), "a.py": (0, 0), "M.py": (0, 0)}),
            _commit({"M.py": (0, 0), "z.py": (0, 0), "a.py": (0, 0)}),
            _commit({"b.py": (0, 0), "c.py": (0, 0)}),
        ],
        min_commits=1,
    )

    assert [(row.together, row.file_a, row.file_b) for row in rows] == [
        (2, "M.py", "a.py"),
        (2, "M.py", "z.py"),
        (2, "a.py", "z.py"),
        (1, "b.py", "c.py"),
    ]
    assert skipped == 0


def test_supplied_pairs_example_renders_exact_report() -> None:
    expected = """TOGETHER    A->B    B->A  FILE A         FILE B
       3   60.0%  100.0%  src/client.py  tests/test_client.py
       2   40.0%  100.0%  src/client.py  src/config.py
       2   40.0%  100.0%  src/client.py  tests/test_config.py
       2  100.0%  100.0%  src/config.py  tests/test_config.py"""

    rows, skipped = analyze(_worked_example_commits())

    assert pairs(rows) == expected
    assert skipped == 0


def test_pairs_report_with_no_rows_is_header_only() -> None:
    assert pairs([]) == "TOGETHER  A->B  B->A  FILE A  FILE B"


def test_pairs_report_uses_singular_notice_when_top_cuts_one_pair() -> None:
    rows = [
        PairRow(3, 2, 4, 3, 3, "a.py", "b.py"),
        PairRow(2, 1, 4, 2, 2, "a.py", "c.py"),
    ]

    rendered = pairs(rows, top=1)

    assert len(rendered.splitlines()) == 3
    assert rendered.endswith("\n... 1 more pair")


def test_pairs_report_uses_plural_notice_when_top_cuts_multiple_pairs() -> None:
    rows = [
        PairRow(4, 2, 4, 4, 4, "a.py", "b.py"),
        PairRow(3, 1, 4, 3, 3, "a.py", "c.py"),
        PairRow(2, 1, 4, 2, 2, "b.py", "c.py"),
    ]

    assert pairs(rows, top=1).endswith("... 2 more pairs")
