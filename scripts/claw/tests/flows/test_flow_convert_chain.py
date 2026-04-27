"""Flow: md → html → docx → pdf chain via pandoc + claw convert."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from .._helpers import invoke_subprocess, require_tool

pytestmark = pytest.mark.flow


def _ok(res) -> None:
    assert res.exit_code == 0, f"exit {res.exit_code}\n{res.output}"


class TestFlowConvertChain:
    @pytest.fixture(scope="class")
    def workspace(self):
        require_tool("pandoc")
        tmp = Path(tempfile.mkdtemp(prefix="claw_flow_conv_"))
        md = tmp / "src.md"
        md.write_text(
            "# Top Heading\n\n"
            "Body with **bold** and a [link](https://example.com).\n\n"
            "## Section A\n\n- one\n- two\n",
            encoding="utf-8",
        )
        ws = {"tmp": tmp, "md": md,
              "html": tmp / "out.html",
              "docx": tmp / "out.docx",
              "pdf_nolatex": tmp / "out-nolatex.pdf"}
        yield ws
        shutil.rmtree(tmp, ignore_errors=True)

    def test_01_md_to_html(self, workspace: dict) -> None:
        _ok(invoke_subprocess("convert", "convert",
                              str(workspace["md"]), str(workspace["html"])))
        assert "Top Heading" in workspace["html"].read_text(encoding="utf-8")

    def test_02_md_to_docx(self, workspace: dict) -> None:
        _ok(invoke_subprocess("convert", "convert",
                              str(workspace["md"]), str(workspace["docx"]),
                              "--standalone"))
        assert workspace["docx"].exists()

    def test_03_md_to_pdf_nolatex(self, workspace: dict) -> None:
        _ok(invoke_subprocess("convert", "md2pdf-nolatex",
                              str(workspace["md"]), str(workspace["pdf_nolatex"])))
        assert workspace["pdf_nolatex"].exists()

    def test_04_book(self, workspace: dict) -> None:
        chapters = [workspace["md"], workspace["md"]]
        out = workspace["tmp"] / "book.html"
        _ok(invoke_subprocess("convert", "book",
                              *(str(c) for c in chapters),
                              "--out", str(out), "--title", "Test Book"))
        assert out.exists()
