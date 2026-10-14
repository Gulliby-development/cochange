from dataclasses import dataclass, field

from .dates import valid_date
from .text import quote


class LogError(Exception):
    """A malformed or unreadable Git-log input error."""


@dataclass
class Commit:
    """One parsed commit and the file changes attributed to it."""

    hash: str
    author: str
    date: str
    files: dict[str, tuple[int, int]] = field(default_factory=dict)


def _valid_count(value: str) -> bool:
    if value == "-":
        return True
    return (
        value == "0"
        or (
            1 <= len(value) <= 9
            and "1" <= value[0] <= "9"
            and all("0" <= digit <= "9" for digit in value[1:])
        )
    )


def expand_path(field: str) -> str:
    """Return the destination path printed by git for a changed or renamed file.

    A malformed rename or an empty destination raises ValueError. The parser adds
    the input display name and physical line number to that diagnostic.
    """
    if not field:
        raise ValueError("empty path")

    if "{" in field or "}" in field:
        if field.count("{") != 1 or field.count("}") != 1:
            raise ValueError("malformed rename")
        open_brace = field.index("{")
        close_brace = field.index("}")
        if close_brace < open_brace:
            raise ValueError("malformed rename")

        prefix = field[:open_brace]
        inside = field[open_brace + 1 : close_brace]
        suffix = field[close_brace + 1 :]
        separator = " => "
        if inside.count(separator) != 1:
            raise ValueError("malformed rename")
        new = inside.split(separator, 1)[1]
        path = (prefix + new + suffix).replace("//", "/")
        if not path:
            raise ValueError("empty path")
        return path

    separator = " => "
    if separator in field:
        _, path = field.split(separator, 1)
        if not path:
            raise ValueError("empty path")
        return path

    return field


def parse_log(display: str, text: str) -> list[Commit]:
    """Parse git-log numstat text into commits, raising LogError on first error."""
    text = text.removeprefix("\ufeff")

    commits: list[Commit] = []
    current: Commit | None = None
    physical_lines = text.split("\n")

    for line_number, raw_line in enumerate(physical_lines, start=1):
        line = raw_line[:-1] if raw_line.endswith("\r") and line_number < len(physical_lines) else raw_line
        if not line:
            continue

        if line.startswith(">"):
            if line.count("\t") < 3:
                problem = 'expected ">HASH<TAB>AUTHOR<TAB>DATE<TAB>SUBJECT"'
                raise LogError(f"{display}:{line_number}: {problem}")

            commit_hash, author, commit_date, _subject = line[1:].split("\t", 3)
            if not (7 <= len(commit_hash) <= 40) or any(
                char not in "0123456789abcdef" for char in commit_hash
            ):
                raise LogError(
                    f'{display}:{line_number}: invalid hash {quote(commit_hash)}'
                )
            if not author:
                raise LogError(f"{display}:{line_number}: empty author")
            if not valid_date(commit_date):
                problem = (
                    f"invalid date {quote(commit_date)} "
                    "(expected a calendar date as YYYY-MM-DD)"
                )
                raise LogError(f"{display}:{line_number}: {problem}")

            current = Commit(commit_hash, author, commit_date)
            commits.append(current)
            continue

        if current is None:
            raise LogError(f"{display}:{line_number}: file line before the first commit")
        if line.count("\t") < 2:
            problem = 'expected "ADDED<TAB>DELETED<TAB>PATH"'
            raise LogError(f"{display}:{line_number}: {problem}")

        added_text, deleted_text, path_field = line.split("\t", 2)
        if not path_field:
            problem = 'expected "ADDED<TAB>DELETED<TAB>PATH"'
            raise LogError(f"{display}:{line_number}: {problem}")
        if not _valid_count(added_text):
            raise LogError(
                f"{display}:{line_number}: invalid count {quote(added_text)}"
            )
        if not _valid_count(deleted_text):
            raise LogError(
                f"{display}:{line_number}: invalid count {quote(deleted_text)}"
            )

        try:
            path = expand_path(path_field)
        except ValueError:
            raise LogError(
                f"{display}:{line_number}: invalid rename {quote(path_field)}"
            ) from None

        added = 0 if added_text == "-" else int(added_text)
        deleted = 0 if deleted_text == "-" else int(deleted_text)
        old_added, old_deleted = current.files.get(path, (0, 0))
        current.files[path] = (old_added + added, old_deleted + deleted)

    return commits
