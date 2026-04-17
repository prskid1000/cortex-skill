"""`--examples` flag: every verb that declares it must produce executable sample
commands. The heuristic is that the example output contains at least one line
starting with `claw ` — the shell prefix of a real invocation.

If no verbs declare `--examples` (current state of the repo), a single
placeholder test documents that the category is empty; the suite stays
discoverable if the convention is added later.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from claw.__main__ import cli

from ._discovery import VERBS_WITH_EXAMPLES_FLAG


if VERBS_WITH_EXAMPLES_FLAG:

    @pytest.mark.parametrize(
        "row",
        VERBS_WITH_EXAMPLES_FLAG,
        ids=[f"{n}-{v}" for n, v, _ in VERBS_WITH_EXAMPLES_FLAG],
    )
    def test_examples_flag_emits_samples(
        runner: CliRunner, row: tuple[str, str, object]
    ) -> None:
        noun, verb, skip_reason = row
        if skip_reason is not None:
            pytest.skip(f"{noun} {verb}: {skip_reason}")
        res = runner.invoke(cli, [noun, verb, "--examples"])
        assert res.exit_code == 0, (
            f"`claw {noun} {verb} --examples` failed: {res.output}"
        )
        assert "claw " in res.output, (
            f"`claw {noun} {verb} --examples` produced no sample line containing "
            f"'claw ':\n{res.output}"
        )

else:

    def test_no_verb_exposes_examples_flag() -> None:
        """Documentary: if this ever fails, populate the parametrized suite above."""
        assert VERBS_WITH_EXAMPLES_FLAG == []
