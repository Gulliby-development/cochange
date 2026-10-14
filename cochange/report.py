from collections.abc import Sequence

from .hot import HotRow
from .owners import OwnerRow
from .pairs import PairRow
from .text import percent, table


def hot(rows: Sequence[HotRow], top: int = 10) -> str:
    """Render the hot-file table and its optional truncation notice."""
    displayed = rows[:top]
    rendered = table(
        [
            ("COMMITS", "ADDED", "DELETED", "AUTHORS", "LAST", "PATH"),
            *[
                (row.commits, row.added, row.deleted, row.authors, row.last, row.path)
                for row in displayed
            ],
        ],
        (True, True, True, True, False, False),
    )
    more = len(rows) - len(displayed)
    if more:
        rendered += f"\n... {more} more {'file' if more == 1 else 'files'}"
    return rendered


def pairs(rows: Sequence[PairRow], top: int = 10) -> str:
    """Render co-change pairs with directional percentages and an optional notice."""
    displayed = rows[:top]
    rendered = table(
        [
            ("TOGETHER", "A->B", "B->A", "FILE A", "FILE B"),
            *[
                (
                    row.together,
                    percent(row.a_together, row.a_commits),
                    percent(row.b_together, row.b_commits),
                    row.file_a,
                    row.file_b,
                )
                for row in displayed
            ],
        ],
        (True, True, True, False, False),
    )
    more = len(rows) - len(displayed)
    if more:
        rendered += f"\n... {more} more {'pair' if more == 1 else 'pairs'}"
    return rendered


def owners(rows: Sequence[OwnerRow], top: int = 10) -> str:
    """Render owner rows, the all-rows author summary, and optional truncation."""
    displayed = rows[:top]
    rendered = table(
        [
            ("COMMITS", "AUTHORS", "SHARE", "OWNER", "PATH"),
            *[
                (
                    row.commits,
                    row.authors,
                    percent(row.owner_commits, row.commits),
                    row.owner,
                    row.path,
                )
                for row in displayed
            ],
        ],
        (True, True, True, False, False),
    )
    if rows:
        single_author = sum(row.authors == 1 for row in rows)
        file_label = "file" if len(rows) == 1 else "files"
        rendered += (
            f"\n{len(rows)} {file_label}, {single_author} with a single author "
            f"({percent(single_author, len(rows))})"
        )

    more = len(rows) - len(displayed)
    if more:
        rendered += f"\n... {more} more {'file' if more == 1 else 'files'}"
    return rendered
