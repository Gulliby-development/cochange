<p align="center"><img src="docs/logo.svg" width="96" alt="" /></p>

# cochange

cochange is an offline command-line tool for people who want to find codebase hotspots, files that change together, and file ownership patterns from a Git repository's history. It reads a text log; it does not run Git, modify the log, or need network access.

[![CI](https://github.com/Gulliby-development/cochange/actions/workflows/ci.yml/badge.svg)](https://github.com/Gulliby-development/cochange/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Why

Reach for it when you want to know where a codebase hurts: which files change most, which files always change together, and who really owns each file. It works from a plain text copy of `git log`, so it needs no Git access, no network and no dependencies.

## Install

Use Python 3.11 or newer. From the repository root, create a virtual environment:

```text
python -m venv .venv
```

Activate that environment using the command for your shell. cochange uses only the Python standard library, so no package installation is required. Run it from the repository root with `python -m cochange`.

## Usage

Create a history log as described in [Log format](#log-format), then choose one of the three commands:

```text
python -m cochange hot [--top N] [--since DATE] [--until DATE] [--path DIR]... LOG
python -m cochange pairs [--top N] [--since DATE] [--until DATE] [--path DIR]... [--min-commits N] [--max-files N] LOG
python -m cochange owners [--top N] [--since DATE] [--until DATE] [--path DIR]... [--min-commits N] LOG
```

Use `-` as LOG to read the log from standard input. The synopsis is also available with `python -m cochange --help`, or with `--help` as the only argument after a command name (`python -m cochange hot --help`):

```text
usage: cochange hot [--top N] [--since DATE] [--until DATE] [--path DIR]... LOG
       cochange pairs [--top N] [--since DATE] [--until DATE] [--path DIR]... [--min-commits N] [--max-files N] LOG
       cochange owners [--top N] [--since DATE] [--until DATE] [--path DIR]... [--min-commits N] LOG
```

The following worked example uses `history.log`. Its contents and the report blocks are reproduced as supplied:

The file `history.log` (`<TAB>` stands for one tab character; the empty lines are skipped by the reader):
```text
>9a8b7c6<TAB>Dana<TAB>2026-03-09<TAB>Retry failed requests
2<TAB>1<TAB>src/client.py
6<TAB>0<TAB>tests/test_client.py

>8f7e6d5<TAB>Eli<TAB>2026-03-05<TAB>Merge branch 'config'

>7e6d5c4<TAB>Eli<TAB>2026-03-04<TAB>Load settings from TOML
10<TAB>4<TAB>src/config.py
3<TAB>3<TAB>src/client.py
1<TAB>1<TAB>tests/test_config.py

>6d5c4b3<TAB>Dana<TAB>2026-03-02<TAB>Move helpers and add a logo
0<TAB>0<TAB>src/{util => helpers}/text.py
-<TAB>-<TAB>docs/logo.png
4<TAB>2<TAB>src/client.py

>5c4b3a2<TAB>Sam<TAB>2026-02-27<TAB>Reformat everything
8<TAB>8<TAB>src/client.py
5<TAB>5<TAB>src/config.py
3<TAB>3<TAB>tests/test_client.py
2<TAB>2<TAB>tests/test_config.py

>4b3a291<TAB>Sam<TAB>2026-02-20<TAB>Add the client
40<TAB>0<TAB>src/client.py
15<TAB>0<TAB>tests/test_client.py
```

`cochange hot --top 3 history.log` prints:

```text
COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH
      5     57       14        3  2026-03-09  src/client.py
      3     24        3        2  2026-03-09  tests/test_client.py
      2     15        9        2  2026-03-04  src/config.py
... 3 more files
```

`cochange pairs history.log` prints:

```text
TOGETHER    A->B    B->A  FILE A         FILE B
       3   60.0%  100.0%  src/client.py  tests/test_client.py
       2   40.0%  100.0%  src/client.py  src/config.py
       2   40.0%  100.0%  src/client.py  tests/test_config.py
       2  100.0%  100.0%  src/config.py  tests/test_config.py
```

`cochange owners history.log` prints:

```text
COMMITS  AUTHORS  SHARE  OWNER  PATH
      5        3  40.0%  Dana   src/client.py
      3        2  66.7%  Sam    tests/test_client.py
2 files, 0 with a single author (0.0%)
```

## Log format

Generate the text log from a Git repository with:

```text
git log --numstat --format=">%H%x09%an%x09%ad%x09%s" --date=short > history.log
```

The file is UTF-8 text. A commit line contains its hash, author, date, and subject separated by tabs; subsequent numstat lines contain added and deleted counts followed by a path. Empty lines are ignored, and merge commits may have no file lines. Git's `-` count represents zero. Rename entries are expanded to the new path, including Git's brace form. The reader accepts LF and CRLF line endings.

## Commands

- **hot** ranks each path by how many selected commits touched it, then by total additions and deletions, and lists the counts, distinct authors, latest date, and path.
- **pairs** finds pairs of paths changed together. Commits touching more than `--max-files` paths are excluded as bulk changes; directional percentages compare a pair's together count with the eligible commits touching each path. `--min-commits` sets the minimum together count.
- **owners** lists paths touched by at least `--min-commits` selected commits, their distinct author count, and the most frequent author. Ties for owner go to the name that sorts first.

All commands accept inclusive `--since` and `--until` dates and `--top` to limit displayed rows. They print tables with deterministic ordering and percentages rounded to one decimal place.

`--path DIR` (repeatable) keeps only the files at or under DIR: a path is kept when it equals DIR or starts with DIR and `/`, so `--path src` keeps `src/client.py` and not `src2/a.py`; a trailing `/` on DIR is ignored. For example, `python -m cochange hot --path src --path docs history.log` ranks only the files under `src` and `docs`. The files are filtered before anything is counted, so every number, the `--max-files` limit of `pairs` and the summary line of `owners` describe the kept files only; a commit left without files still counts as selected.

## Version

Pass `--version` as the only argument to print the program name and its version on standard output and exit with 0; no log is read:

```text
python -m cochange --version
```

prints:

```text
cochange 0.1.0
```

The number is the `version` of `pyproject.toml`. `--version` together with any other argument is not recognized: `--version hot` is the unknown command `"--version"` and `hot --version LOG` the unknown option `"--version"`. The usage text printed by `--help` is unchanged.

## Exit codes

- `0`: success.
- `1`: no commit is in the selected date range.
- `2`: usage or input error.

## Development

Run the project's checks from its root:

```text
ruff check .
pytest -q
```

## License

MIT, see [LICENSE](LICENSE).

---

Built with BAKED, an open-source coding agent (bench loop round 26).
