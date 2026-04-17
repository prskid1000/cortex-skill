"""Every verb in `VERBS` must surface in its parent noun's --help output.

One parametrization per (noun, verb) pair — if a single verb is ever dropped
from the LazyGroup registration, exactly that test fails. Keeps diagnostics
precise instead of a single assert-all-verbs failure that hides the culprit.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from claw.__main__ import cli

from ._discovery import NOUN_VERB_PAIRS


@pytest.mark.parametrize(
    "noun,verb",
    NOUN_VERB_PAIRS,
    ids=[f"{n}-{v}" for n, v in NOUN_VERB_PAIRS],
)
def test_noun_help_lists_verb(runner: CliRunner, noun: str, verb: str) -> None:
    res = runner.invoke(cli, [noun, "--help"])
    assert res.exit_code == 0, f"`claw {noun} --help` failed: {res.output}"
    assert verb in res.output, (
        f"verb {verb!r} missing from `claw {noun} --help`:\n{res.output}"
    )
