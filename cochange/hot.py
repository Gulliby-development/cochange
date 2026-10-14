from collections.abc import Iterable, Mapping
from typing import NamedTuple

from .gitlog import Commit


class HotRow(NamedTuple):
    commits: int
    added: int
    deleted: int
    authors: int
    last: str
    path: str


def analyze(commits: Iterable[Mapping[str, object] | Commit]) -> list[HotRow]:
    """Aggregate selected commits into deterministically ordered hot-file rows."""
    totals: dict[str, dict[str, object]] = {}

    for commit in commits:
        if isinstance(commit, Commit):
            author = commit.author
            date = commit.date
            files = commit.files
        else:
            author = commit["author"]
            date = commit["date"]
            files = commit["files"]
        if not isinstance(author, str) or not isinstance(date, str):
            raise TypeError("commit author and date must be strings")
        if not isinstance(files, Mapping):
            raise TypeError("commit files must be a mapping")

        for path, counts in files.items():
            if not isinstance(path, str):
                raise TypeError("file paths must be strings")
            added, deleted = counts
            aggregate = totals.setdefault(
                path,
                {"commits": 0, "added": 0, "deleted": 0, "authors": set(), "last": date},
            )
            aggregate["commits"] = int(aggregate["commits"]) + 1
            aggregate["added"] = int(aggregate["added"]) + added
            aggregate["deleted"] = int(aggregate["deleted"]) + deleted
            authors = aggregate["authors"]
            if not isinstance(authors, set):
                raise TypeError("invalid author accumulator")
            authors.add(author)
            if date > str(aggregate["last"]):
                aggregate["last"] = date

    rows = [
        HotRow(
            int(values["commits"]),
            int(values["added"]),
            int(values["deleted"]),
            len(values["authors"]),
            str(values["last"]),
            path,
        )
        for path, values in totals.items()
    ]
    return sorted(rows, key=lambda row: (-row.commits, -(row.added + row.deleted), row.path))
