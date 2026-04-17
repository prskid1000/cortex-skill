"""Lightweight JSON-output smoke tests for pure-function, read-only verbs.

These target verbs that accept a path to an existing fixture and a `--json`
flag and produce a JSON document on stdout — the typical `read`, `meta`, and
`stat` pattern. Each case provides an input fixture built by the conftest
helpers. If a fixture dependency (e.g. reportlab) is missing the test skips.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from claw.__main__ import cli


# (label, argv_prefix, extra_argv, fixture_name)
# - argv_prefix is the noun/verb (/subverb) tuple — inserted before the fixture path
# - extra_argv is appended after the fixture path (flags like --sheet, --json)
# - fixture_name is the name of a fixture defined in conftest.py
#
# Dropped (speculative / require extra fixtures we don't want to fabricate here):
#   img-stat, img-meta, html-meta, html-links — verbs don't exist
#   xml-validate — needs a real --xsd schema, not a smoke-test concern
_CASES: list[tuple[str, tuple[str, ...], list[str], str]] = [
    # xlsx
    ("xlsx-read",      ("xlsx", "read"),           ["--json"], "sample_xlsx"),
    ("xlsx-meta-get",  ("xlsx", "meta", "get"),    ["--json"], "sample_xlsx"),
    ("xlsx-stat",      ("xlsx", "stat"),           ["--sheet", "Data", "--json"], "sample_xlsx"),
    ("xlsx-pivots-list", ("xlsx", "pivots", "list"), ["--json"], "sample_xlsx"),
    # docx — requires python-docx; fixture guards with importorskip
    ("docx-meta-get",      ("docx", "meta", "get"),          ["--json"], "sample_docx"),
    ("docx-comments-dump", ("docx", "comments", "dump"),     ["--json"], "sample_docx"),
    # pdf
    ("pdf-info",     ("pdf", "info"),        ["--json"], "sample_pdf"),
    ("pdf-meta-get", ("pdf", "meta", "get"), ["--json"], "sample_pdf"),
    ("pdf-toc-get",  ("pdf", "toc", "get"),  ["--json"], "sample_pdf"),
    # pptx
    ("pptx-meta-get", ("pptx", "meta", "get"), ["--json"], "sample_pptx"),
]


@pytest.mark.parametrize(
    "label,argv_prefix,extra,fixture_name",
    _CASES,
    ids=[c[0] for c in _CASES],
)
def test_json_output_parses(
    request: pytest.FixtureRequest,
    runner: CliRunner,
    label: str,
    argv_prefix: tuple[str, ...],
    extra: list[str],
    fixture_name: str,
) -> None:
    try:
        factory: Callable[..., Path] = request.getfixturevalue(fixture_name)
    except pytest.skip.Exception:
        raise
    except Exception as exc:
        pytest.skip(f"fixture {fixture_name} unavailable: {exc}")
    try:
        fixture_path = factory()
    except pytest.skip.Exception:
        raise
    except Exception as exc:
        pytest.skip(f"fixture {fixture_name} build failed: {exc}")
    res = runner.invoke(cli, [*argv_prefix, str(fixture_path), *extra])
    assert res.exit_code == 0, (
        f"`claw {' '.join(argv_prefix)} --json` failed (exit={res.exit_code}): {res.output!r}"
    )
    payload = (res.output or "").strip()
    assert payload, f"{' '.join(argv_prefix)}: no stdout captured"
    try:
        json.loads(payload)
    except json.JSONDecodeError:
        # Some verbs also print a header line in front of JSON; try last block.
        last = payload.splitlines()[-1]
        json.loads(last)
