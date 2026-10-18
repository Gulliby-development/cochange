from dataclasses import dataclass

from .dates import valid_date
from .text import quote

USAGE = """usage: cochange hot [--top N] [--since DATE] [--until DATE] [--path DIR]... LOG
       cochange pairs [--top N] [--since DATE] [--until DATE] [--path DIR]... [--min-commits N] [--max-files N] LOG
       cochange owners [--top N] [--since DATE] [--until DATE] [--path DIR]... [--min-commits N] LOG"""


class ArgumentError(Exception):
    """A command-line usage error."""


class HelpRequested(Exception):
    """The sole --help argument was supplied."""


@dataclass(frozen=True)
class Arguments:
    command: str
    top: int
    since: str | None
    until: str | None
    min_commits: int
    max_files: int
    log: str
    paths: tuple[str, ...] = ()


def _number(value: str, option: str, minimum: int, maximum: int) -> int:
    if value == "0":
        number = 0
    elif (
        not value
        or value[0] == "0"
        or any(char < "0" or char > "9" for char in value)
    ):
        raise ArgumentError(
            f"invalid {option} {quote(value)} "
            f"(expected a whole number from {minimum} to {maximum})"
        )
    elif len(value) > len(str(maximum)):
        number = maximum + 1
    else:
        number = int(value)

    if number < minimum or number > maximum:
        raise ArgumentError(
            f"invalid {option} {quote(value)} "
            f"(expected a whole number from {minimum} to {maximum})"
        )
    return number


def parse_args(argv: list[str] | tuple[str, ...]) -> Arguments:
    """Parse and validate the command line without using argparse."""
    if list(argv) == ["--help"]:
        raise HelpRequested

    if not argv:
        raise ArgumentError("missing command (hot, pairs or owners)")

    command = argv[0]
    if command not in {"hot", "pairs", "owners"}:
        raise ArgumentError(f"unknown command {quote(command)}")

    if len(argv) == 2 and argv[1] == "--help":
        raise HelpRequested

    option_limits = {
        "--top": (1, 1000),
        "--since": None,
        "--until": None,
        "--path": None,
        "--min-commits": (1, 100000),
        "--max-files": (2, 1000),
    }
    values: dict[str, str] = {}
    path_values: list[str] = []
    seen: set[str] = set()
    positional: list[str] = []
    index = 1

    while index < len(argv):
        argument = argv[index]
        option = next(
            (
                candidate
                for candidate in option_limits
                if argument == candidate or argument.startswith(candidate + "=")
            ),
            None,
        )
        if option is not None:
            if argument == option:
                if index + 1 >= len(argv):
                    raise ArgumentError(f"{option} needs a value")
                index += 1
                value = argv[index]
            else:
                value = argument[len(option) + 1 :]
            if option == "--path":
                path_values.append(value)
            else:
                seen.add(option)
                values[option] = value
        elif argument.startswith("-") and argument != "-":
            raise ArgumentError(f"unknown option {quote(argument)}")
        else:
            positional.append(argument)
        index += 1

    top_text = values.get("--top", "10")
    top = _number(top_text, "--top", 1, 1000)

    since = values.get("--since")
    if since is not None and not valid_date(since):
        raise ArgumentError(
            f'invalid --since {quote(since)} (expected a date as YYYY-MM-DD)'
        )

    until = values.get("--until")
    if until is not None and not valid_date(until):
        raise ArgumentError(
            f'invalid --until {quote(until)} (expected a date as YYYY-MM-DD)'
        )

    paths = []
    for value in path_values:
        path = value.rstrip("/")
        if not path:
            raise ArgumentError(
                f"invalid --path {quote(value)} (expected a directory or file path)"
            )
        paths.append(path)

    default_minimum = 3 if command == "owners" else 2
    min_text = values.get("--min-commits", str(default_minimum))
    min_commits = _number(min_text, "--min-commits", 1, 100000)

    max_text = values.get("--max-files", "30")
    max_files = _number(max_text, "--max-files", 2, 1000)

    if "--max-files" in seen and command != "pairs":
        raise ArgumentError("--max-files is only valid for pairs")
    if "--min-commits" in seen and command == "hot":
        raise ArgumentError("--min-commits is not valid for hot")
    if since is not None and until is not None and since > until:
        raise ArgumentError("--since is after --until")
    if not positional:
        raise ArgumentError("missing LOG")
    if len(positional) > 1:
        raise ArgumentError("too many arguments")

    return Arguments(
        command=command,
        top=top,
        since=since,
        until=until,
        min_commits=min_commits,
        max_files=max_files,
        log=positional[0],
        paths=tuple(paths),
    )
