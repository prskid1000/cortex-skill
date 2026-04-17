"""Per-flag help coverage.

For every `@click.option` declared on every verb, assert that the flag name is
present in the `claw <noun> <verb> --help` output. This guarantees the Click
decorator actually attached — a regression where `@common_output_options` gets
dropped would immediately surface here as hundreds of failures.

Parameters are generated at import time by walking `VERBS` dicts and the Click
command's `.params` attribute.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from claw.__main__ import cli

from ._discovery import FLAG_PARAMS


def _id(row: tuple[str, str, str, object]) -> str:
    noun, verb, flag, _ = row
    return f"{noun}-{verb}-{flag}"


@pytest.mark.parametrize("row", FLAG_PARAMS, ids=[_id(r) for r in FLAG_PARAMS])
def test_flag_appears_in_help(runner: CliRunner, row: tuple[str, str, str, object]) -> None:
    noun, verb, flag, skip_reason = row
    if skip_reason is not None:
        pytest.skip(f"{noun} {verb}: {skip_reason}")
    res = runner.invoke(cli, [noun, verb, "--help"])
    assert res.exit_code == 0, f"{noun} {verb} --help failed: {res.output}"
    assert flag in res.output, (
        f"flag {flag!r} missing from `claw {noun} {verb} --help`:\n{res.output}"
    )
