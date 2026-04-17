"""Usage-error exit-code contracts.

Two suites:

- `test_missing_required_arg_exits_2` — every verb that declares at least one
  required positional argument must exit 2 when invoked with no args.
- `test_unknown_flag_exits_2` — every verb must reject a bogus long flag with
  exit code 2, regardless of its argument shape (Click processes options
  before validating argument counts).
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from claw.__main__ import cli

from ._discovery import ALL_VERBS, VERBS_WITH_REQUIRED_ARGS


_BOGUS_FLAG = "--definitely-not-a-flag-xxxxx"


@pytest.mark.parametrize(
    "row",
    VERBS_WITH_REQUIRED_ARGS,
    ids=[f"{n}-{v}" for n, v, _ in VERBS_WITH_REQUIRED_ARGS],
)
def test_missing_required_arg_exits_2(
    runner: CliRunner, row: tuple[str, str, object]
) -> None:
    noun, verb, skip_reason = row
    if skip_reason is not None:
        pytest.skip(f"{noun} {verb}: {skip_reason}")
    res = runner.invoke(cli, [noun, verb])
    assert res.exit_code == 2, (
        f"expected Click usage-error (2) for bare `claw {noun} {verb}`, got "
        f"{res.exit_code}:\n{res.output}"
    )


@pytest.mark.parametrize(
    "row",
    ALL_VERBS,
    ids=[f"{n}-{v}" for n, v, _ in ALL_VERBS],
)
def test_unknown_flag_exits_2(
    runner: CliRunner, row: tuple[str, str, object]
) -> None:
    noun, verb, skip_reason = row
    if skip_reason is not None:
        pytest.skip(f"{noun} {verb}: {skip_reason}")
    res = runner.invoke(cli, [noun, verb, _BOGUS_FLAG])
    assert res.exit_code == 2, (
        f"expected Click usage-error (2) for unknown flag on `claw {noun} "
        f"{verb}`, got {res.exit_code}:\n{res.output}"
    )
