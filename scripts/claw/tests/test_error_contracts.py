"""Tier 4 — exit codes and structured error shape."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from claw.__main__ import cli


# ---- missing input file ---------------------------------------------------- #

@pytest.mark.parametrize("argv", [
    ["xlsx", "read", "/def/not/here.xlsx"],
    ["pdf", "info", "/def/not/here.pdf"],
    ["docx", "read", "/def/not/here.docx"],
    ["img", "resize", "/def/not/here.png",
     "--geometry", "10x10", "--out", "/tmp/x.png"],
])
def test_missing_file_exits_2(runner: CliRunner, argv: list[str]) -> None:
    # Click's built-in exists=True gates fail with exit=2 BEFORE the command runs.
    res = runner.invoke(cli, argv)
    assert res.exit_code == 2, res.output
    assert "does not exist" in res.output.lower() or \
        "no such" in res.output.lower()


# ---- bad flag (click usage error) ----------------------------------------- #

@pytest.mark.parametrize("argv", [
    ["xlsx", "new", "--not-a-flag"],
    ["pdf", "rotate", "--by", "77"],  # not in Choice
    ["img", "thumb", "--max", "not-an-int"],
    ["xlsx", "chart", "--type", "wobble"],
])
def test_bad_flag_exits_2(runner: CliRunner, argv: list[str]) -> None:
    res = runner.invoke(cli, argv)
    assert res.exit_code == 2, res.output


# ---- unknown verb ---------------------------------------------------------- #

def test_unknown_verb_exits_2(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["xlsx", "not-a-verb"])
    assert res.exit_code == 2
    assert "no such command" in res.output.lower() or \
        "unknown command" in res.output.lower()


def test_unknown_noun_exits_2(runner: CliRunner) -> None:
    res = runner.invoke(cli, ["definitelynotanoun"])
    assert res.exit_code == 2


# ---- overwrite without --force → FileExistsError (exit 1) ------------------ #

def test_overwrite_without_force(runner: CliRunner, tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    out = tmp_path / "o.xlsx"
    first = runner.invoke(cli, ["xlsx", "new", str(out)])
    assert first.exit_code == 0, first.output
    second = runner.invoke(cli, ["xlsx", "new", str(out)])
    assert second.exit_code == 1
    assert isinstance(second.exception, FileExistsError)


def test_force_overwrites(runner: CliRunner, tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    out = tmp_path / "o.xlsx"
    runner.invoke(cli, ["xlsx", "new", str(out)])
    res = runner.invoke(cli, ["xlsx", "new", str(out), "--force"])
    assert res.exit_code == 0, res.output


def test_backup_creates_bak(runner: CliRunner, tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    out = tmp_path / "o.xlsx"
    runner.invoke(cli, ["xlsx", "new", str(out)])
    res = runner.invoke(cli, ["xlsx", "new", str(out), "--force", "--backup"])
    assert res.exit_code == 0, res.output
    assert (tmp_path / "o.xlsx.bak").exists()


# ---- --json error output --------------------------------------------------- #

def test_json_error_on_missing_dependency(runner: CliRunner, tmp_path: Path) -> None:
    """An error emitted with --json must be valid JSON with required keys.

    We drive a path that is guaranteed to error — convert list-formats without
    pandoc — but only on systems without pandoc. Fall back to a safe stand-in.
    """
    import shutil as _sh
    if _sh.which("pandoc") is not None:
        pytest.skip("pandoc is installed; cannot exercise the missing-tool path")
    res = runner.invoke(cli, ["convert", "list-formats", "--json"])
    # stderr contains the JSON error payload.
    blob = res.stderr or res.output
    payload = json.loads(blob.strip().splitlines()[-1])
    assert "error" in payload
    assert "code" in payload


# ---- safe_write mkdir contract ------------------------------------------- #

def test_missing_parent_dir_without_mkdir(runner: CliRunner,
                                            tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    out = tmp_path / "nope" / "deep" / "o.xlsx"
    res = runner.invoke(cli, ["xlsx", "new", str(out)])
    assert res.exit_code == 1
    assert isinstance(res.exception, FileNotFoundError)


def test_missing_parent_dir_with_mkdir(runner: CliRunner,
                                         tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    out = tmp_path / "nope" / "deep" / "o.xlsx"
    res = runner.invoke(cli, ["xlsx", "new", str(out), "--mkdir"])
    assert res.exit_code == 0, res.output
    assert out.exists()


# ---- unknown --type values (click.Choice enforces) ------------------------ #

def test_xlsx_chart_unknown_type_exit_2(runner: CliRunner,
                                         sample_xlsx) -> None:
    p = sample_xlsx()
    res = runner.invoke(cli, ["xlsx", "chart", str(p),
                              "--sheet", "Data", "--type", "nope",
                              "--data", "B2:B4"])
    assert res.exit_code == 2
    assert "invalid" in res.output.lower() or "choose" in res.output.lower()


# ---- xlsx read of a non-xlsx (input guarded by click, exit 2) ------------- #

def test_xlsx_read_non_xlsx(runner: CliRunner, tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    p = tmp_path / "fake.xlsx"
    p.write_text("not an xlsx", encoding="utf-8")
    res = runner.invoke(cli, ["xlsx", "read", str(p)])
    # openpyxl raises on bad format; wrapper may surface 1.
    assert res.exit_code != 0


# ---- dry-run writes nothing ----------------------------------------------- #

def test_dry_run_writes_nothing(runner: CliRunner, tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    out = tmp_path / "dry.xlsx"
    res = runner.invoke(cli, ["xlsx", "new", str(out), "--dry-run"])
    assert res.exit_code == 0, res.output
    assert not out.exists()
