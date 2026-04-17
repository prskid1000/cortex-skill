"""Direct unit tests for claw.common helpers — selectors, geometry, safe_write."""

from __future__ import annotations

from pathlib import Path

import pytest

from claw.common.geometry import Geometry
from claw.common.safe import safe_write
from claw.common.selectors import NodeSelector, PageSelector, RangeSelector


# --- PageSelector -----------------------------------------------------------

@pytest.mark.parametrize("spec,total,expected", [
    ("1", 10, [1]),
    ("1-5", 10, [1, 2, 3, 4, 5]),
    ("1,3,5", 10, [1, 3, 5]),
    ("1-3,7,9-end", 10, [1, 2, 3, 7, 9, 10]),
    ("all", 4, [1, 2, 3, 4]),
    ("odd", 5, [1, 3, 5]),
    ("even", 6, [2, 4, 6]),
    ("z-1", 3, [3, 2, 1]),
    ("reverse", 3, [3, 2, 1]),
    ("", 3, [1, 2, 3]),
    ("5,5,5", 10, [5]),
    ("3-1", 5, [3, 2, 1]),
    ("end", 4, [4]),
    ("100", 10, []),
])
def test_page_selector(spec: str, total: int, expected: list[int]) -> None:
    assert PageSelector(spec).resolve(total) == expected


# --- RangeSelector ----------------------------------------------------------

@pytest.mark.parametrize("spec,expected", [
    ("A1", (1, 1, None, None)),
    ("A1:D10", (1, 1, 10, 4)),
    ("B2:Z99", (2, 2, 99, 26)),
    ("AA1:AB2", (1, 27, 2, 28)),
])
def test_range_selector(spec: str, expected: tuple) -> None:
    assert RangeSelector(spec).resolve() == expected


def test_range_selector_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        RangeSelector("not-a-range").resolve()


# --- NodeSelector -----------------------------------------------------------

@pytest.mark.parametrize("raw,kind", [
    ("/root/a", "xpath"),
    (".//p", "xpath"),
    ("div.class", "css"),
    ("#id", "css"),
    ("a[href]", "css"),
])
def test_node_selector_kind(raw: str, kind: str) -> None:
    assert NodeSelector(raw).kind == kind


# --- Geometry ---------------------------------------------------------------

@pytest.mark.parametrize("spec,w,h,expected", [
    ("100x200", 400, 400, (100, 100)),      # min-scale (default)
    ("50%", 200, 100, (100, 50)),
    ("100x200!", 10, 10, (100, 200)),       # forced
    ("100x200>", 50, 50, (50, 50)),         # shrink-only: smaller kept
    ("100x^", 100, 50, (100, 50)),
    ("100", 200, 100, (100, 50)),
])
def test_geometry_apply(spec: str, w: int, h: int, expected: tuple[int, int]) -> None:
    assert Geometry.parse(spec).apply_to(w, h) == expected


def test_geometry_offset() -> None:
    g = Geometry.parse("100x100+5+6")
    assert g.offset == (5, 6)


def test_geometry_fill_min() -> None:
    g = Geometry.parse("100x200^")
    assert g.fill_min is True


def test_geometry_empty() -> None:
    g = Geometry.parse("")
    assert g.apply_to(50, 50) == (50, 50)


# --- safe_write -------------------------------------------------------------

def _write_hi(f) -> None:
    f.write(b"hi")


def test_safe_write_atomic(tmp_path: Path) -> None:
    out = tmp_path / "a.bin"
    safe_write(out, _write_hi)
    assert out.read_bytes() == b"hi"


def test_safe_write_refuses_overwrite_without_force(tmp_path: Path) -> None:
    out = tmp_path / "a.bin"
    safe_write(out, _write_hi)
    with pytest.raises(FileExistsError):
        safe_write(out, _write_hi)


def test_safe_write_force_overwrites(tmp_path: Path) -> None:
    out = tmp_path / "a.bin"
    safe_write(out, _write_hi)
    safe_write(out, lambda f: f.write(b"new"), force=True)
    assert out.read_bytes() == b"new"


def test_safe_write_backup_creates_bak(tmp_path: Path) -> None:
    out = tmp_path / "a.bin"
    safe_write(out, _write_hi)
    safe_write(out, lambda f: f.write(b"new"), force=True, backup=True)
    assert out.with_suffix(".bin.bak").read_bytes() == b"hi"
    assert out.read_bytes() == b"new"


def test_safe_write_mkdir(tmp_path: Path) -> None:
    out = tmp_path / "sub" / "dir" / "a.bin"
    safe_write(out, _write_hi, mkdir=True)
    assert out.read_bytes() == b"hi"


def test_safe_write_no_mkdir_raises(tmp_path: Path) -> None:
    out = tmp_path / "nope" / "a.bin"
    with pytest.raises(FileNotFoundError):
        safe_write(out, _write_hi)


def test_safe_write_cleans_tempfile_on_error(tmp_path: Path) -> None:
    out = tmp_path / "a.bin"
    def boom(f) -> None:
        raise RuntimeError("boom")
    with pytest.raises(RuntimeError):
        safe_write(out, boom)
    # No .claw-* leftovers.
    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(".claw-")]
    assert leftovers == []
