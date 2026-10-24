"""Tests for the standalone --version argument."""

import io
import tomllib
from pathlib import Path

import pytest

from cochange.cli import main


def _run(argv: list[str]) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    code = main(argv, io.BytesIO(b""), stdout, stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_version_alone_prints_the_name_and_the_number() -> None:
    assert _run(["--version"]) == (0, "cochange 0.1.0\n", "")


def test_version_matches_pyproject() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    version = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]

    assert _run(["--version"]) == (0, f"cochange {version}\n", "")


def test_version_reads_no_log() -> None:
    stdout, stderr = io.StringIO(), io.StringIO()

    code = main(["--version"], io.BytesIO(b"not a log"), stdout, stderr)

    assert (code, stdout.getvalue(), stderr.getvalue()) == (0, "cochange 0.1.0\n", "")


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["--version", "hot"], 'cochange: unknown command "--version"\n'),
        (["--version", "--version"], 'cochange: unknown command "--version"\n'),
        (["--version=1"], 'cochange: unknown command "--version=1"\n'),
        (["hot", "--version", "x.log"], 'cochange: unknown option "--version"\n'),
        (["pairs", "x.log", "--version"], 'cochange: unknown option "--version"\n'),
        (["-V"], 'cochange: unknown command "-V"\n'),
    ],
)
def test_version_next_to_other_arguments_is_still_an_error(argv: list[str], message: str) -> None:
    assert _run(argv) == (2, "", message)


def test_help_text_is_unchanged() -> None:
    code, out, err = _run(["--help"])

    assert code == 0
    assert out.startswith("usage: cochange hot [--top N]")
    assert "--version" not in out
    assert err == ""
