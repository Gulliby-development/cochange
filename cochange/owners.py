from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import NamedTuple


class OwnerRow(NamedTuple):
    commits: int
    authors: int
    owner_commits: int
    owner: str
    path: str


def analyze(
    commits: Iterable[Mapping[str, object]],
    min_commits: int = 3,
) -> list[OwnerRow]:
    """Find qualifying files and their most frequent author."""
    by_path: dict[str, Counter[str]] = defaultdict(Counter)

    for commit in commits:
        author = commit["author"]
        files = commit["files"]
        if not isinstance(author, str):
            raise TypeError("commit author must be a string")
        if not isinstance(files, Mapping):
            raise TypeError("commit files must be a mapping")

        for path in files:
            if not isinstance(path, str):
                raise TypeError("file paths must be strings")
            by_path[path][author] += 1

    rows = []
    for path, author_counts in by_path.items():
        commits_for_path = sum(author_counts.values())
        if commits_for_path < min_commits:
            continue
        owner = min(author_counts, key=lambda name: (-author_counts[name], name))
        rows.append(
            OwnerRow(
                commits_for_path,
                len(author_counts),
                author_counts[owner],
                owner,
                path,
            )
        )

    return sorted(rows, key=lambda row: (-row.commits, row.path))
