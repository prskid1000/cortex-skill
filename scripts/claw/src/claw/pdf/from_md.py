"""claw pdf from-md — Markdown → PDF via reportlab (default), pymupdf, or pandoc."""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, run, safe_write


PAGE_SIZES = ("Letter", "A4", "Legal")
THEMES = ("minimal", "corporate", "academic", "dark")
ENGINES = ("reportlab", "pymupdf", "pandoc")

_BULLET_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")


def _parse_margin(spec: str) -> float:
    s = spec.strip().lower()
    for suf, mult in (("in", 72.0), ("cm", 28.3465), ("mm", 2.83465), ("pt", 1.0)):
        if s.endswith(suf):
            return float(s[: -len(suf)]) * mult
    return float(s)


def _inline(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2">\1</link>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", text)
    return text


def _parse_table(lines: list[str], i: int):
    if "|" not in lines[i] or i + 1 >= len(lines):
        return None, i
    if not re.match(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$", lines[i + 1]):
        return None, i
    rows = [[c.strip() for c in lines[i].strip().strip("|").split("|")]]
    j = i + 2
    while j < len(lines) and "|" in lines[j] and lines[j].strip():
        rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
        j += 1
    return rows, j


def _nested_list(block: list[str], styles, LF, LI, P):
    items, kind = [], None
    i = 0
    while i < len(block):
        m = _BULLET_RE.match(block[i])
        if not m or len(m.group(1)) > 0:
            break
        kind = kind or ("1" if m.group(2)[:-1].isdigit() else "bullet")
        para = P(_inline(m.group(3)), styles["BodyText"])
        i += 1
        sub: list[str] = []
        while i < len(block) and block[i].startswith((" ", "\t")) and _BULLET_RE.match(block[i]):
            sub.append(block[i].lstrip())
            i += 1
        if sub:
            items.append(LI(para))
            items.append(LI(_nested_list(sub, styles, LF, LI, P), leftIndent=18))
        else:
            items.append(LI(para))
    return LF(items, bulletType=(kind or "bullet"), leftIndent=18, bulletFontSize=9)


def _reportlab_story(text: str, src: Path, title, author, styles, code_style):
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import (Paragraph, Spacer, Preformatted, ListFlowable,
                                    ListItem, Table, TableStyle, Image)
    story: list = []
    if title:
        story.append(Paragraph(title, styles["Title"]))
        if author:
            story.append(Paragraph(author, styles["Italic"]))
        story.append(Spacer(1, 18))
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            story += [Preformatted("\n".join(buf), code_style), Spacer(1, 8)]
            i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            base = styles.get(f"Heading{min(level, 4)}", styles["Heading1"])
            hs = base.clone(name=f"H{level}_toc")
            hs.level = level - 1
            story.append(Paragraph(m.group(2), hs))
            i += 1; continue
        tbl, nxt = _parse_table(lines, i)
        if tbl:
            data = [[Paragraph(_inline(c), styles["BodyText"]) for c in r] for r in tbl]
            t = Table(data, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story += [t, Spacer(1, 8)]
            i = nxt; continue
        img = re.match(r"^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if img:
            p = (src.parent / img.group(2)).resolve()
            if p.exists():
                try:
                    from PIL import Image as PIL
                    with PIL.open(p) as pil:
                        iw, ih = pil.size
                    scale = min(1.0, (6.5 * inch) / iw)
                    story.append(Image(str(p), width=iw * scale, height=ih * scale))
                except Exception:
                    story.append(Image(str(p), width=6 * inch, height=3 * inch))
                story.append(Spacer(1, 6))
            i += 1; continue
        if _BULLET_RE.match(line):
            block = []
            while i < len(lines) and (_BULLET_RE.match(lines[i]) or
                                      (lines[i].startswith((" ", "\t")) and block)):
                block.append(lines[i]); i += 1
            story += [_nested_list(block, styles, ListFlowable, ListItem, Paragraph),
                      Spacer(1, 6)]
            continue
        if not line.strip():
            story.append(Spacer(1, 6)); i += 1; continue
        para = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|```|[-*+]\s|\d+\.\s|\|)", lines[i].strip()):
            para.append(lines[i]); i += 1
        story.append(Paragraph(_inline(" ".join(para)), styles["BodyText"]))
    return story


def _build_reportlab(src, out, theme, size, mgn, toc, title, author, force, backup, mkdir):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, PageBreak
    from reportlab.platypus.tableofcontents import TableOfContents

    styles = getSampleStyleSheet()
    if theme == "dark":
        for n in ("BodyText", "Heading1", "Heading2", "Heading3"):
            styles[n].textColor = colors.whitesmoke
    if theme == "academic":
        styles["BodyText"].fontName = "Times-Roman"
    code_style = ParagraphStyle("code", parent=styles["Code"], fontSize=9,
                                leftIndent=12, backColor=colors.whitesmoke)
    story = _reportlab_story(src.read_text(encoding="utf-8"), src, title, author, styles, code_style)

    if toc:
        tf = TableOfContents()
        tf.levelStyles = [ParagraphStyle(name=f"TOC{n}", fontSize=12 - n, leftIndent=20 * (n + 1),
                                         firstLineIndent=-20, spaceBefore=6 - n, leading=16 - n)
                          for n in range(3)]
        head: list = []
        if title:
            head.append(Paragraph(title, styles["Title"]))
            if author:
                head.append(Paragraph(author, styles["Italic"]))
            head.append(PageBreak())
        head += [Paragraph("Contents", styles["Heading1"]), tf, PageBreak()]
        story = head + story

    def build(f):
        doc = BaseDocTemplate(f, pagesize=size, leftMargin=mgn, rightMargin=mgn,
                              topMargin=mgn, bottomMargin=mgn,
                              title=title or src.stem, author=author or "")
        doc.addPageTemplates([PageTemplate(id="main",
            frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")])])

        def after(flow):
            s = getattr(flow, "style", None)
            if s and getattr(s, "name", "").startswith("H") and hasattr(s, "level"):
                doc.notify("TOCEntry", (s.level, flow.getPlainText(), doc.page))
        doc.afterFlowable = after
        (doc.multiBuild if toc else doc.build)(story)

    safe_write(out, build, force=force, backup=backup, mkdir=mkdir)


def _build_pymupdf(src, out, size, mgn, force, backup, mkdir):
    try:
        import fitz
        import markdown as md_lib
    except ImportError:
        die("pymupdf engine requires: pip install 'claw[pdf]' markdown")
    html = f"<html><body>{md_lib.markdown(src.read_text(encoding='utf-8'), extensions=['tables', 'fenced_code', 'toc'])}</body></html>"
    w, h = size
    rect = fitz.Rect(mgn, mgn, w - mgn, h - mgn)

    def build(f):
        fd, tmp = tempfile.mkstemp(prefix=".claw-md-", suffix=".pdf"); os.close(fd)
        try:
            story = fitz.Story(html=html)
            wr = fitz.DocumentWriter(tmp)
            more, pages = True, 0
            while more:
                dev = wr.begin_page(fitz.Rect(0, 0, w, h))
                more, _ = story.place(rect); story.draw(dev); wr.end_page()
                pages += 1
                if pages > 10000:
                    die("runaway page generation (>10000)")
            wr.close()
            f.write(Path(tmp).read_bytes())
        finally:
            try: os.unlink(tmp)
            except OSError: pass
    safe_write(out, build, force=force, backup=backup, mkdir=mkdir)


def _build_pandoc(src, out, page_size, margin, toc, title, author, force, backup, mkdir):
    fd, tmp = tempfile.mkstemp(prefix=".claw-pandoc-", suffix=".pdf"); os.close(fd)
    args = [str(src), "-o", tmp, "-V", f"papersize={page_size.lower()}",
            "-V", f"geometry:margin={margin}"]
    if toc: args.append("--toc")
    if title: args += ["-M", f"title={title}"]
    if author: args += ["-M", f"author={author}"]
    try:
        run("pandoc", *args)
        data = Path(tmp).read_bytes()
    finally:
        try: os.unlink(tmp)
        except OSError: pass
    safe_write(out, lambda f: f.write(data), force=force, backup=backup, mkdir=mkdir)


@click.command(name="from-md")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("out", type=click.Path(path_type=Path))
@click.option("--theme", type=click.Choice(THEMES), default="minimal")
@click.option("--page-size", type=click.Choice(PAGE_SIZES), default="Letter")
@click.option("--margin", default="1in")
@click.option("--toc", is_flag=True)
@click.option("--title", default=None)
@click.option("--author", default=None)
@click.option("--engine", type=click.Choice(ENGINES), default="reportlab")
@common_output_options
def from_md(src: Path, out: Path, theme: str, page_size: str, margin: str,
            toc: bool, title: str | None, author: str | None, engine: str,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Convert Markdown <SRC> to PDF <OUT>."""
    mgn = _parse_margin(margin)
    if dry_run:
        click.echo(f"would render {src} → {out} ({engine}, {theme}, {page_size})")
        return
    if engine == "pandoc":
        _build_pandoc(src, out, page_size, margin, toc, title, author, force, backup, mkdir)
    else:
        try:
            from reportlab.lib import pagesizes
        except ImportError:
            die("reportlab not installed; install: pip install 'claw[pdf]'")
        size = getattr(pagesizes, page_size, None) or getattr(pagesizes, page_size.lower())
        if engine == "pymupdf":
            _build_pymupdf(src, out, size, mgn, force, backup, mkdir)
        else:
            _build_reportlab(src, out, theme, size, mgn, toc, title, author,
                             force, backup, mkdir)
    if as_json:
        emit_json({"out": str(out), "engine": engine, "theme": theme,
                   "page_size": page_size, "toc": toc})
    elif not quiet:
        click.echo(f"wrote {out}")
