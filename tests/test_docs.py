"""Check that the README contains the required documentation and examples."""

import re
from pathlib import Path

_USAGE = """usage: cochange hot [--top N] [--since DATE] [--until DATE] LOG
       cochange pairs [--top N] [--since DATE] [--until DATE] [--min-commits N] [--max-files N] LOG
       cochange owners [--top N] [--since DATE] [--until DATE] [--min-commits N] LOG"""

_HISTORY_INTRO = (
    "The file `history.log` (`<TAB>` stands for one tab character; "
    "the empty lines are skipped by the reader):"
)
_HISTORY = """>9a8b7c6<TAB>Dana<TAB>2026-03-09<TAB>Retry failed requests
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
15<TAB>0<TAB>tests/test_client.py"""

_HOT_OUTPUT = """COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH
      5     57       14        3  2026-03-09  src/client.py
      3     24        3        2  2026-03-09  tests/test_client.py
      2     15        9        2  2026-03-04  src/config.py
... 3 more files"""

_PAIRS_OUTPUT = """TOGETHER    A->B    B->A  FILE A         FILE B
       3   60.0%  100.0%  src/client.py  tests/test_client.py
       2   40.0%  100.0%  src/client.py  src/config.py
       2   40.0%  100.0%  src/client.py  tests/test_config.py
       2  100.0%  100.0%  src/config.py  tests/test_config.py"""

_OWNERS_OUTPUT = """COMMITS  AUTHORS  SHARE  OWNER  PATH
      5        3  40.0%  Dana   src/client.py
      3        2  66.7%  Sam    tests/test_client.py
2 files, 0 with a single author (0.0%)"""

_OUTPUT_EXAMPLES = (_HOT_OUTPUT, _PAIRS_OUTPUT, _OWNERS_OUTPUT)


def _read_readme() -> str:
    path = Path(__file__).resolve().parents[1] / "README.md"
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_readme_has_the_required_headings() -> None:
    headings = {
        "## Install",
        "## Usage",
        "## Log format",
        "## Commands",
        "## Exit codes",
        "## Development",
    }

    assert headings <= set(_read_readme().splitlines())


def test_readme_covers_setup_commands_log_generation_and_development() -> None:
    readme = _read_readme()

    required_text = (
        "cochange is an offline command-line tool",
        "python -m venv .venv",
        "python -m cochange",
        'git log --numstat --format=">%H%x09%an%x09%ad%x09%s" --date=short > history.log',
        "ruff check .",
        "pytest -q",
        "`0`: success.",
        "`1`: no commit is in the selected date range.",
        "`2`: usage or input error.",
    )
    for text in required_text:
        assert text in readme


def test_readme_contains_the_supplied_usage_and_history_verbatim() -> None:
    readme = _read_readme()

    assert _USAGE in readme
    assert _HISTORY_INTRO in readme
    assert _HISTORY in readme


def test_readme_contains_only_the_three_supplied_output_examples() -> None:
    readme = _read_readme()
    text_blocks = re.findall(r"```text\n(.*?)\n```", readme, flags=re.DOTALL)
    output_headers = (
        "COMMITS  ADDED  DELETED  AUTHORS  LAST        PATH",
        "TOGETHER    A->B    B->A  FILE A         FILE B",
        "COMMITS  AUTHORS  SHARE  OWNER  PATH",
    )
    output_blocks = tuple(
        block for block in text_blocks if block.startswith(output_headers)
    )

    assert output_blocks == _OUTPUT_EXAMPLES
