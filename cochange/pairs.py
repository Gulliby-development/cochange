from collections import Counter
from collections.abc import Iterable, Mapping
from typing import NamedTuple


class PairRow(NamedTuple):
    together: int
    a_together: int
    a_commits: int
    b_together: int
    b_commits: int
    file_a: str
    file_b: str


def analyze(
    commits: Iterable[Mapping[str, object]],
    min_commits: int = 2,
    max_files: int = 30,
) -> tuple[list[PairRow], int]:
    """Return qualifying pair rows and the number of excluded bulk commits."""
    together: Counter[tuple[str, str]] = Counter()
    touched: Counter[str] = Counter()
    skipped = 0

    for commit in commits:
        files = commit["files"]
        if not isinstance(files, Mapping):
            raise TypeError("commit files must be a mapping")
        paths = sorted(files)
        if len(paths) > max_files:
            skipped += 1
            continue

        touched.update(paths)
        for index, file_a in enumerate(paths):
            for file_b in paths[index + 1 :]:
                together[(file_a, file_b)] += 1

    rows = [
        PairRow(
            count,
            count,
            touched[file_a],
            count,
            touched[file_b],
            file_a,
            file_b,
        )
        for (file_a, file_b), count in together.items()
        if count >= min_commits
    ]
    rows.sort(key=lambda row: (-row.together, row.file_a, row.file_b))
    return rows, skipped
