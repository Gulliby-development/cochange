import pytest

from cochange.gitlog import Commit, LogError, expand_path, parse_log
from cochange.text import quote


def commit_line(
    commit_hash: str = "abcdef0",
    author: str = "Dana",
    date: str = "2026-03-09",
    subject: str = "subject",
) -> str:
    return f">{commit_hash}\t{author}\t{date}\t{subject}"


def assert_log_error(text: str, expected: str, display: str = "history.log") -> None:
    with pytest.raises(LogError) as error:
        parse_log(display, text)
    assert str(error.value) == expected


def test_parse_commit_and_file_fields() -> None:
    text = (
        commit_line(subject="Retry failed requests\twith context")
        + "\n2\t1\tsrc/client.py\n"
        + "-\t0\tdocs/logo.png\n"
    )

    assert parse_log("history.log", text) == [
        Commit(
            "abcdef0",
            "Dana",
            "2026-03-09",
            {"src/client.py": (2, 1), "docs/logo.png": (0, 0)},
        )
    ]


def test_subject_may_be_empty() -> None:
    assert parse_log("history.log", commit_line(subject="")) == [
        Commit("abcdef0", "Dana", "2026-03-09", {})
    ]


def test_tabbed_subject_does_not_change_following_file_line() -> None:
    text = commit_line(subject="first\tsecond\tthird") + "\n1\t2\tfile.txt"

    assert parse_log("history.log", text)[0].files == {"file.txt": (1, 2)}


@pytest.mark.parametrize("text", ["", "\n", "\n\n", "\ufeff", "\ufeff\n"])
def test_empty_input_and_empty_lines_have_no_commits(text: str) -> None:
    assert parse_log("history.log", text) == []


def test_skips_one_leading_bom_and_parses_crlf() -> None:
    text = (
        "\ufeff"
        + commit_line(date="2024-02-29")
        + "\r\n\r\n"
        + "3\t4\tfile.txt\r\n"
    )

    assert parse_log("history.log", text) == [
        Commit("abcdef0", "Dana", "2024-02-29", {"file.txt": (3, 4)})
    ]


def test_only_one_leading_bom_is_skipped() -> None:
    text = "\ufeff\ufeff" + commit_line()

    assert_log_error(
        text,
        'history.log:1: file line before the first commit',
    )


def test_line_number_counts_blank_physical_lines() -> None:
    text = commit_line() + "\n\n\n1\t2\t"

    assert_log_error(
        text,
        'history.log:4: expected "ADDED<TAB>DELETED<TAB>PATH"',
    )


def test_cr_without_following_lf_is_preserved_in_path() -> None:
    text = commit_line() + "\n0\t0\tfile.txt\r"

    assert parse_log("history.log", text)[0].files == {"file.txt\r": (0, 0)}


@pytest.mark.parametrize("hash_length", [7, 40])
def test_hash_length_boundaries_are_accepted(hash_length: int) -> None:
    commit_hash = "a" * hash_length

    assert parse_log("history.log", commit_line(commit_hash=commit_hash))[0].hash == commit_hash


@pytest.mark.parametrize(
    "commit_hash",
    ["abcdef", "a" * 41, "ABCDEF1", "abcdefg!", "abcdefg١"],
)
def test_invalid_hash_is_reported_exactly(commit_hash: str) -> None:
    assert_log_error(
        commit_line(commit_hash=commit_hash),
        f"history.log:1: invalid hash {quote(commit_hash)}",
    )


def test_hash_error_precedes_empty_author_and_bad_date() -> None:
    assert_log_error(
        commit_line(commit_hash="ABC", author="", date="not-a-date"),
        'history.log:1: invalid hash "ABC"',
    )


def test_empty_author_precedes_bad_date() -> None:
    assert_log_error(
        commit_line(author="", date="2026-02-30"),
        "history.log:1: empty author",
    )


@pytest.mark.parametrize(
    "commit_date",
    ["2026-02-30", "0000-01-01", "2026-2-01", "٢٠٢٦-02-01", "2026-03-01x"],
)
def test_invalid_commit_date_is_reported_exactly(commit_date: str) -> None:
    assert_log_error(
        commit_line(date=commit_date),
        f"history.log:1: invalid date {quote(commit_date)} (expected a calendar date as YYYY-MM-DD)",
    )


def test_real_leap_day_is_accepted() -> None:
    assert parse_log("history.log", commit_line(date="2024-02-29"))[0].date == "2024-02-29"


def test_commit_line_requires_three_tabs() -> None:
    assert_log_error(
        ">abcdef0\tDana\t2026-03-09",
        'history.log:1: expected ">HASH<TAB>AUTHOR<TAB>DATE<TAB>SUBJECT"',
    )


def test_subject_may_contain_more_than_three_tabs() -> None:
    text = commit_line(subject="one\ttwo\tthree\tfour")

    assert parse_log("history.log", text)[0].hash == "abcdef0"


def test_file_line_before_first_commit_is_an_error() -> None:
    assert_log_error(
        "1\t2\tfile.txt",
        "history.log:1: file line before the first commit",
    )


@pytest.mark.parametrize("file_line", ["1", "1\t2"])
def test_file_line_requires_two_tabs(file_line: str) -> None:
    assert_log_error(
        commit_line() + "\n" + file_line,
        'history.log:2: expected "ADDED<TAB>DELETED<TAB>PATH"',
    )


def test_file_line_requires_nonempty_path() -> None:
    assert_log_error(
        commit_line() + "\n1\t2\t",
        'history.log:2: expected "ADDED<TAB>DELETED<TAB>PATH"',
    )


@pytest.mark.parametrize("count", ["-", "0", "9", "999999999"])
def test_valid_count_forms_are_accepted(count: str) -> None:
    files = parse_log("history.log", commit_line() + f"\n{count}\t{count}\tfile.txt")[0].files

    numeric_count = 0 if count == "-" else int(count)
    assert files == {"file.txt": (numeric_count, numeric_count)}


@pytest.mark.parametrize(
    "count",
    ["", "00", "01", "+1", "-1", "1.0", " 1", "1 ", "١", "1000000000"],
)
def test_invalid_added_count_is_reported_exactly(count: str) -> None:
    assert_log_error(
        commit_line() + f"\n{count}\t0\tfile.txt",
        f"history.log:2: invalid count {quote(count)}",
    )


@pytest.mark.parametrize("count", ["", "00", "01", "+1", "-1", "1.0", "١", "1000000000"])
def test_invalid_deleted_count_is_reported_exactly(count: str) -> None:
    assert_log_error(
        commit_line() + f"\n0\t{count}\tfile.txt",
        f"history.log:2: invalid count {quote(count)}",
    )


def test_added_count_is_validated_before_deleted_count() -> None:
    assert_log_error(
        commit_line() + "\nx\tbad\tfile.txt",
        'history.log:2: invalid count "x"',
    )


def test_deleted_count_is_validated_before_rename() -> None:
    assert_log_error(
        commit_line() + "\n0\tbad\t{old => new}",
        'history.log:2: invalid count "bad"',
    )


@pytest.mark.parametrize(
    ("field", "expected_path"),
    [
        ("old.txt => new.txt", "new.txt"),
        ("src/{old => new}/file.c", "src/new/file.c"),
        ("src/{ => sub}/f.c", "src/sub/f.c"),
        ("src/{sub => }/f.c", "src/f.c"),
        ("src//{old => new}//file.c", "src/new/file.c"),
        ("plain/file.c", "plain/file.c"),
        ("no spaces=>arrow.txt", "no spaces=>arrow.txt"),
        ("old name => new name", "new name"),
    ],
)
def test_expand_path_supported_forms(field: str, expected_path: str) -> None:
    assert expand_path(field) == expected_path


@pytest.mark.parametrize(
    "field",
    [
        "",
        "old => ",
        "{ => }",
        "{old => new",
        "old => new}",
        "{old new}",
        "{old => new => other}",
        "{a => b}/{c => d}",
        "{{a => b}}",
        "}",
    ],
)
def test_expand_path_rejects_empty_or_malformed_renames(field: str) -> None:
    with pytest.raises(ValueError):
        expand_path(field)


@pytest.mark.parametrize(
    "field",
    ["src/{a => b", "src/a}", "src/{a b}", "src/{a => b}/{c => d}"],
)
def test_parser_reports_invalid_rename_with_quoted_field(field: str) -> None:
    assert_log_error(
        commit_line() + f"\n0\t0\t{field}",
        f"history.log:2: invalid rename {quote(field)}",
    )


def test_rename_error_follows_count_validation() -> None:
    assert_log_error(
        commit_line() + "\nnot-a-count\t0\t{old => new}",
        'history.log:2: invalid count "not-a-count"',
    )


def test_paths_are_preserved_after_the_third_tab() -> None:
    path = "folder with spaces/file\tname.txt"
    text = commit_line() + f"\n1\t0\t{path}"

    assert parse_log("history.log", text)[0].files == {path: (1, 0)}


def test_parser_expands_empty_rename_sides() -> None:
    text = commit_line() + "\n1\t1\tsrc/{ => sub}/f.c\n2\t0\tsrc/{sub => }/g.c"

    assert parse_log("history.log", text)[0].files == {
        "src/sub/f.c": (1, 1),
        "src/g.c": (2, 0),
    }


def test_duplicate_resolved_paths_sum_counts_once() -> None:
    text = (
        commit_line()
        + "\n1\t1\ta.txt"
        + "\n2\t0\told.txt => a.txt"
        + "\n-\t3\t{old => a.txt}"
    )

    assert parse_log("history.log", text)[0].files == {"a.txt": (3, 4)}


def test_merge_commit_has_no_files_and_is_retained() -> None:
    text = commit_line(subject="merge") + "\n" + commit_line(
        commit_hash="1234567",
        author="Eli",
        subject="next",
    )

    assert parse_log("history.log", text) == [
        Commit("abcdef0", "Dana", "2026-03-09", {}),
        Commit("1234567", "Eli", "2026-03-09", {}),
    ]


def test_first_error_across_lines_is_reported() -> None:
    text = commit_line() + "\n01\t0\tfirst.txt\n1\t1\t{bad"

    assert_log_error(text, 'history.log:2: invalid count "01"')


def test_display_name_is_included_in_parser_errors() -> None:
    assert_log_error(
        "1\t2\tfile.txt",
        "custom/history.log:1: file line before the first commit",
        display="custom/history.log",
    )
