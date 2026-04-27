"""Unit tests for `claw convert` (pandoc-driven)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from .._helpers import assert_ok, invoke, require_tool

NOUN = "convert"


def test_help(runner: CliRunner) -> None:
    res = invoke(runner, NOUN, "--help")
    assert_ok(res)


class TestConvert:
    def test_md_to_html(self, runner: CliRunner, tmp_path: Path, sample_md_rich) -> None:
        require_tool("pandoc")
        out = tmp_path / "out.html"
        invoke(runner, NOUN, "convert", str(sample_md_rich()), str(out))
        assert out.exists()
        assert "Top Heading" in out.read_text(encoding="utf-8")

    def test_md_to_docx(self, runner: CliRunner, tmp_path: Path, sample_md_rich) -> None:
        require_tool("pandoc")
        out = tmp_path / "out.docx"
        invoke(runner, NOUN, "convert", str(sample_md_rich()), str(out), "--standalone")
        assert out.exists()


class TestBook:
    def test_html(self, runner: CliRunner, tmp_path: Path, sample_md_rich) -> None:
        require_tool("pandoc")
        ch1 = sample_md_rich(name="ch1.md")
        ch2 = sample_md_rich(name="ch2.md")
        out = tmp_path / "book.html"
        invoke(runner, NOUN, "book", str(ch1), str(ch2),
               "--out", str(out), "--title", "MyBook")
        assert out.exists()


class TestSlides:
    def test_reveal(self, runner: CliRunner, tmp_path: Path) -> None:
        require_tool("pandoc")
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\nbody\n\n# Slide 2\n\nbody2\n", encoding="utf-8")
        out = tmp_path / "slides.html"
        invoke(runner, NOUN, "slides", str(md),
               "--format", "reveal", "--out", str(out))
        assert out.exists()


class TestListFormats:
    def test_in(self, runner: CliRunner) -> None:
        require_tool("pandoc")
        res = invoke(runner, NOUN, "list-formats", "--direction", "in")
        assert_ok(res)


class TestMd2pdfNolatex:
    def test_basic(self, runner: CliRunner, tmp_path: Path, sample_md_rich) -> None:
        out = tmp_path / "n.pdf"
        invoke(runner, NOUN, "md2pdf-nolatex", str(sample_md_rich()), str(out))
        assert out.exists()
