"""Shared fixtures and helpers for the claw test suite."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "external_tool(name): requires an external CLI tool (pandoc, ffmpeg, ...).",
    )
    config.addinivalue_line("markers", "network: requires network access.")
    config.addinivalue_line("markers", "slow: slower test, may exceed 1s.")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--no-network", action="store_true",
                     help="Skip tests marked with @pytest.mark.network.")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--no-network"):
        skip = pytest.mark.skip(reason="--no-network was passed")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip)


def skip_without(tool: str) -> None:
    """Skip current test if <tool> is not on PATH."""
    if shutil.which(tool) is None:
        pytest.skip(f"external tool {tool!r} not on PATH")


@pytest.fixture
def runner() -> CliRunner:
    """A fresh CliRunner; mix_stderr defaults vary across click versions."""
    return CliRunner()


@pytest.fixture
def sample_csv(tmp_path: Path) -> Callable[..., Path]:
    def _make(rows: int = 3, name: str = "data.csv", header: tuple[str, ...] = ("a", "b", "c")) -> Path:
        p = tmp_path / name
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            for i in range(rows):
                w.writerow([f"r{i}", i, i * 10])
        return p
    return _make


@pytest.fixture
def sample_xlsx(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "book.xlsx", sheet: str = "Data",
              rows: list[list] | None = None) -> Path:
        openpyxl = pytest.importorskip("openpyxl")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet
        ws.append(["a", "b", "c"])
        for r in (rows if rows is not None else [[1, 2, 3], [4, 5, 6], [7, 8, 9]]):
            ws.append(r)
        p = tmp_path / name
        wb.save(p)
        return p
    return _make


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "doc.pdf", pages: int = 2) -> Path:
        pytest.importorskip("reportlab")
        from reportlab.pdfgen import canvas
        p = tmp_path / name
        c = canvas.Canvas(str(p))
        for i in range(pages):
            c.drawString(72, 720, f"Page {i + 1} hello world")
            c.showPage()
        c.save()
        return p
    return _make


@pytest.fixture
def sample_png(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "img.png", size: tuple[int, int] = (100, 100),
              color: tuple[int, int, int] = (200, 50, 50)) -> Path:
        Image = pytest.importorskip("PIL.Image")
        p = tmp_path / name
        im = Image.new("RGB", size, color)
        im.save(p, format="PNG")
        return p
    return _make


@pytest.fixture
def sample_html(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "page.html",
              body: str = "<h1>T</h1><p>hi</p><a href='/x'>x</a>") -> Path:
        p = tmp_path / name
        p.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")
        return p
    return _make


@pytest.fixture
def sample_xml(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "doc.xml",
              body: str = "<root><a>1</a><a>2</a></root>") -> Path:
        p = tmp_path / name
        p.write_text(f'<?xml version="1.0"?>{body}', encoding="utf-8")
        return p
    return _make


@pytest.fixture
def sample_md(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "doc.md", body: str = "# T\n\nBody para.\n") -> Path:
        p = tmp_path / name
        p.write_text(body, encoding="utf-8")
        return p
    return _make


@pytest.fixture
def sample_json_rows(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "rows.json",
              rows: list[dict] | None = None) -> Path:
        rows = rows or [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}]
        p = tmp_path / name
        p.write_text(json.dumps(rows), encoding="utf-8")
        return p
    return _make


@pytest.fixture
def sample_pptx(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "deck.pptx") -> Path:
        pptx = pytest.importorskip("pptx")
        prs = pptx.Presentation()
        prs.slides.add_slide(prs.slide_layouts[0])
        p = tmp_path / name
        prs.save(p)
        return p
    return _make


@pytest.fixture
def sample_docx(tmp_path: Path) -> Callable[..., Path]:
    def _make(name: str = "doc.docx") -> Path:
        docx = pytest.importorskip("docx")
        d = docx.Document()
        d.add_heading("Title", level=1)
        d.add_paragraph("Body paragraph.")
        p = tmp_path / name
        d.save(p)
        return p
    return _make


@pytest.fixture
def sample_mp4(tmp_path: Path) -> Callable[..., Path]:
    """Synthesize a tiny mp4 via ffmpeg. Skip if ffmpeg is absent."""
    def _make(name: str = "clip.mp4", seconds: int = 1) -> Path:
        if shutil.which("ffmpeg") is None:
            pytest.skip("ffmpeg not on PATH")
        import subprocess
        p = tmp_path / name
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "lavfi", "-i", f"color=c=blue:s=128x128:d={seconds}",
             "-pix_fmt", "yuv420p", str(p)],
            check=True,
        )
        return p
    return _make
