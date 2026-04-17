"""Shared test-discovery helpers.

Walks the `claw.__main__.NOUNS` dispatch table and their VERBS to produce
parameter lists that drive the generated test suites. Any per-verb module that
fails to import (missing heavy dep) yields a single skip-marked entry instead
of erroring the collection phase.
"""

from __future__ import annotations

import importlib
from typing import Any

import click

from claw.__main__ import NOUNS

# Nouns that are plain commands, not groups — they have no VERBS dict.
_PLAIN_COMMANDS = {"doctor", "completion"}


def _noun_verb_items() -> list[tuple[str, str, tuple[str, str]]]:
    out: list[tuple[str, str, tuple[str, str]]] = []
    for noun in NOUNS:
        if noun in _PLAIN_COMMANDS:
            continue
        try:
            mod = importlib.import_module(f"claw.{noun}")
        except Exception:
            continue
        verbs = getattr(mod, "VERBS", None)
        if not verbs:
            continue
        for v_name, spec in verbs.items():
            out.append((noun, v_name, spec))
    out.sort(key=lambda t: (t[0], t[1]))
    return out


NOUN_VERB_ITEMS: list[tuple[str, str, tuple[str, str]]] = _noun_verb_items()


def _load_cmd(noun: str, verb: str, spec: tuple[str, str]) -> click.Command | str:
    """Return the click command object, or a string describing the import error."""
    mod_path, attr = spec
    try:
        mod = importlib.import_module(mod_path)
    except Exception as exc:
        return f"import failed: {exc}"
    cmd = getattr(mod, attr, None)
    if cmd is None:
        return f"module {mod_path} missing attribute {attr!r}"
    return cmd


def flag_params() -> list[tuple[str, str, str, Any]]:
    """Yield (noun, verb, flag, skip_reason_or_None) for every click.Option on every verb.

    skip_reason is a string when the verb failed to load (the test will skip).
    """
    rows: list[tuple[str, str, str, Any]] = []
    for noun, verb, spec in NOUN_VERB_ITEMS:
        cmd = _load_cmd(noun, verb, spec)
        if isinstance(cmd, str):
            rows.append((noun, verb, "<load-failure>", cmd))
            continue
        for p in cmd.params:
            if not isinstance(p, click.Option):
                continue
            long_opts = [o for o in p.opts if o.startswith("--")]
            opt = long_opts[0] if long_opts else (p.opts[0] if p.opts else "")
            if not opt:
                continue
            rows.append((noun, verb, opt, None))
    return rows


def verbs_with_required_args() -> list[tuple[str, str, Any]]:
    """Yield (noun, verb, skip_reason_or_None) for verbs declaring at least one required Argument."""
    rows: list[tuple[str, str, Any]] = []
    for noun, verb, spec in NOUN_VERB_ITEMS:
        cmd = _load_cmd(noun, verb, spec)
        if isinstance(cmd, str):
            rows.append((noun, verb, cmd))
            continue
        has_req = any(isinstance(p, click.Argument) and p.required for p in cmd.params)
        if has_req:
            rows.append((noun, verb, None))
    return rows


def all_verbs() -> list[tuple[str, str, Any]]:
    """Yield (noun, verb, skip_reason_or_None) for every verb regardless of arg shape."""
    rows: list[tuple[str, str, Any]] = []
    for noun, verb, spec in NOUN_VERB_ITEMS:
        cmd = _load_cmd(noun, verb, spec)
        if isinstance(cmd, str):
            rows.append((noun, verb, cmd))
            continue
        rows.append((noun, verb, None))
    return rows


def verbs_with_examples_flag() -> list[tuple[str, str, Any]]:
    """Yield (noun, verb, skip_reason_or_None) for verbs whose click options include '--examples'."""
    rows: list[tuple[str, str, Any]] = []
    for noun, verb, spec in NOUN_VERB_ITEMS:
        cmd = _load_cmd(noun, verb, spec)
        if isinstance(cmd, str):
            continue
        if any(
            isinstance(p, click.Option) and "--examples" in p.opts
            for p in cmd.params
        ):
            rows.append((noun, verb, None))
    return rows


def noun_verb_pairs() -> list[tuple[str, str]]:
    """Every (noun, verb) pair, ignoring import status — for noun-level help coverage."""
    return [(n, v) for n, v, _ in NOUN_VERB_ITEMS]


FLAG_PARAMS = flag_params()
VERBS_WITH_REQUIRED_ARGS = verbs_with_required_args()
ALL_VERBS = all_verbs()
VERBS_WITH_EXAMPLES_FLAG = verbs_with_examples_flag()
NOUN_VERB_PAIRS = noun_verb_pairs()
