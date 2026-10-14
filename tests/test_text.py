import pytest

from cochange.text import percent, quote, table


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", '""'),
        ("plain ASCII", '"plain?ASCII"'),
        ('a"b', '"a"b"'),
        ("space and\ttab", '"space?and?tab"'),
        ("line\r\nbreak", '"line??break"'),
        ("café🙂", '"caf??"'),
        ("~\x7f", '"~?"'),
    ],
)
def test_quote_displays_non_printable_and_non_ascii_code_points_as_question_marks(
    value: str, expected: str
) -> None:
    assert quote(value) == expected


@pytest.mark.parametrize(
    ("part", "whole", "expected"),
    [
        (0, 16, "0.0%"),
        (1, 16, "6.3%"),
        (1, 3, "33.3%"),
        (2, 3, "66.7%"),
        (1, 8, "12.5%"),
        (1, 20, "5.0%"),
        (3, 3, "100.0%"),
    ],
)
def test_percent_rounds_half_up_to_one_decimal(part: int, whole: int, expected: str) -> None:
    assert percent(part, whole) == expected


def test_table_aligns_columns_and_uses_code_point_widths() -> None:
    rendered = table(
        [
            ("NAME", "COUNT", "LAST"),
            ("é", 2, "x"),
            ("long", 10, "last"),
        ],
        [False, True, False],
    )

    assert rendered == "NAME  COUNT  LAST\né         2  x\nlong     10  last"


def test_table_leaves_the_last_column_unpadded() -> None:
    rendered = table(
        [
            ("A", "LONG"),
            ("WIDER", "x"),
        ],
        [False, False],
    )

    assert rendered == "A      LONG\nWIDER  x"
    assert all(line == line.rstrip(" ") for line in rendered.split("\n"))


def test_table_uses_lf_between_rows_without_platform_line_endings() -> None:
    rendered = table([("A", "B"), ("a", "b")], [False, False])

    assert rendered == "A  B\na  b"
    assert "\r" not in rendered


def test_table_with_no_rows_is_empty() -> None:
    assert table([], []) == ""
