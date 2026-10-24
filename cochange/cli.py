import sys
from collections.abc import Sequence
from typing import BinaryIO, TextIO

from .args import USAGE, ArgumentError, Arguments, HelpRequested, parse_args
from .gitlog import LogError, parse_log
from .hot import analyze as analyze_hot
from .owners import analyze as analyze_owners
from .pairs import analyze as analyze_pairs
from .report import hot as render_hot
from .report import owners as render_owners
from .report import pairs as render_pairs

VERSION = "0.1.0"


def _display_name(path: str) -> str:
    return "<stdin>" if path == "-" else path.replace("\\", "/")


def _write_error(stderr: TextIO, message: str) -> None:
    print(f"cochange: {message}", file=stderr)


def _read_input(arguments: Arguments, stdin: BinaryIO) -> str:
    if arguments.log == "-":
        raw = stdin.read()
    else:
        try:
            with open(arguments.log, "rb") as source:
                raw = source.read()
        except OSError:
            raise LogError(f"{_display_name(arguments.log)}: cannot read the file") from None

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise LogError(f"{_display_name(arguments.log)}: input is not valid UTF-8") from None


def main(
    argv: Sequence[str],
    stdin: BinaryIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the CLI with injectable streams for tests."""
    if stdin is None:
        stdin = sys.stdin.buffer
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    if list(argv) == ["--version"]:
        print(f"cochange {VERSION}", file=stdout)
        return 0

    try:
        arguments = parse_args(list(argv))
    except HelpRequested:
        print(USAGE, file=stdout)
        return 0
    except ArgumentError as error:
        _write_error(stderr, str(error))
        return 2

    try:
        text = _read_input(arguments, stdin)
    except LogError as error:
        _write_error(stderr, str(error))
        return 2

    display = _display_name(arguments.log)
    try:
        commits = parse_log(display, text)
    except LogError as error:
        _write_error(stderr, str(error))
        return 2

    if not commits:
        _write_error(stderr, f"{display}: no commits")
        return 2

    selected = [
        commit
        for commit in commits
        if (arguments.since is None or commit.date >= arguments.since)
        and (arguments.until is None or commit.date <= arguments.until)
    ]
    if not selected:
        _write_error(stderr, "no commits in the selected range")
        return 1

    analysis_commits = [
        {
            "author": commit.author,
            "date": commit.date,
            "files": {
                path: changes
                for path, changes in commit.files.items()
                if not arguments.paths
                or any(
                    path == directory or path.startswith(directory + "/")
                    for directory in arguments.paths
                )
            },
        }
        for commit in selected
    ]
    if arguments.command == "hot":
        rendered = render_hot(analyze_hot(analysis_commits), arguments.top)
        print(rendered, file=stdout)
        return 0

    if arguments.command == "pairs":
        rows, skipped = analyze_pairs(
            analysis_commits,
            min_commits=arguments.min_commits,
            max_files=arguments.max_files,
        )
        print(render_pairs(rows, arguments.top), file=stdout)
        if skipped:
            commit_label = "commit" if skipped == 1 else "commits"
            _write_error(
                stderr,
                f"skipped {skipped} {commit_label} with more than "
                f"{arguments.max_files} files",
            )
        return 0

    rendered = render_owners(
        analyze_owners(analysis_commits, min_commits=arguments.min_commits), arguments.top
    )
    print(rendered, file=stdout)
    return 0
