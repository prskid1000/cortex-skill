"""Tier 1 — help/discovery for every noun and every verb.

Every invocation must exit 0, emit non-empty stdout, and contain no traceback.
"""

from __future__ import annotations

import importlib

import pytest
from click.testing import CliRunner

from claw.__main__ import NOUNS, cli


NOUN_GROUPS = [name for name in NOUNS if name not in ("doctor", "completion", "help")]


def _no_traceback(output: str) -> None:
    assert "Traceback" not in output, output


def _verb_list(noun: str) -> list[str]:
    mod = importlib.import_module(f"claw.{noun}")
    verbs = getattr(mod, "VERBS", None)
    return sorted(verbs.keys()) if verbs else []


NOUN_VERB_PAIRS = sorted(
    [(n, v) for n in NOUN_GROUPS for v in _verb_list(n)]
)


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_top_level_help(runner: CliRunner, flag: str) -> None:
    res = runner.invoke(cli, [flag])
    assert res.exit_code == 0
    assert "claw" in res.output.lower() or "usage" in res.output.lower()
    _no_traceback(res.output)


def test_version(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["--version"])
    assert res.exit_code == 0
    assert "version" in res.output.lower()


def test_help_all(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["--help-all"])
    assert res.exit_code == 0
    assert len(res.output) > 500


def test_help_alias_noun_verb(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["help", "xlsx", "from-csv"])
    assert res.exit_code == 0
    assert "csv" in res.output.lower()


def test_help_alias_empty_prints_root(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["help"])
    assert res.exit_code == 0
    assert "usage" in res.output.lower()


def test_help_alias_unknown_exits_2(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["help", "nope-nope"])
    assert res.exit_code == 2


@pytest.mark.parametrize("noun", NOUN_GROUPS + ["doctor", "completion"])
def test_noun_help(runner: CliRunner, noun: str) -> None:
    res = runner.invoke(cli, [noun, "--help"])
    assert res.exit_code == 0, res.output
    assert "usage" in res.output.lower()
    _no_traceback(res.output)


@pytest.mark.parametrize("noun,verb", NOUN_VERB_PAIRS)
def test_verb_help(runner: CliRunner, noun: str, verb: str) -> None:
    res = runner.invoke(cli, [noun, verb, "--help"])
    assert res.exit_code == 0, res.output
    assert res.output.strip(), f"{noun} {verb} produced empty help"
    _no_traceback(res.output)


def test_noun_list_commands_lists_every_verb(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["xlsx", "--help"])
    for verb in _verb_list("xlsx"):
        assert verb in res.output


def test_verb_catalog_size() -> None:
    assert len(NOUN_VERB_PAIRS) >= 100
