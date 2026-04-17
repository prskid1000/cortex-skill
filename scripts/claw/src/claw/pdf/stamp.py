"""claw pdf stamp — overlay an image on pages via PyMuPDF."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import PageSelector, common_output_options, die, emit_json, safe_write


ANCHORS = ("TL", "TR", "BL", "BR", "C")


def _anchor_rect(anchor: str, page_w: float, page_h: float,
                 img_w: float, img_h: float,
                 ox: float, oy: float):
    import fitz
    if anchor == "TL":
        x0, y0 = ox, oy
    elif anchor == "TR":
        x0, y0 = page_w - img_w - ox, oy
    elif anchor == "BL":
        x0, y0 = ox, page_h - img_h - oy
    elif anchor == "BR":
        x0, y0 = page_w - img_w - ox, page_h - img_h - oy
    else:
        x0, y0 = (page_w - img_w) / 2 + ox, (page_h - img_h) / 2 + oy
    return fitz.Rect(x0, y0, x0 + img_w, y0 + img_h)


@click.command(name="stamp")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--image", required=True,
              type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--scale", type=float, default=0.2,
              help="Fraction of page width (0..1).")
@click.option("--at", "anchor", type=click.Choice(ANCHORS), default="TR")
@click.option("--offset", default="20,20", help="x,y offset from anchor in points.")
@click.option("--opacity", type=float, default=1.0)
@click.option("--pages", default="all")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def stamp(src: Path, image: Path, scale: float, anchor: str, offset: str,
          opacity: float, pages: str, out: Path | None, in_place: bool,
          force: bool, backup: bool, as_json: bool, dry_run: bool,
          quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Stamp an --image onto pages of <SRC>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    try:
        ox, oy = (float(v) for v in offset.split(","))
    except ValueError:
        die("--offset must be x,y", code=2)

    doc = fitz.open(str(src))
    try:
        total = doc.page_count
        target_pages = set(PageSelector(pages).resolve(total))
        pix = fitz.Pixmap(str(image))
        try:
            aspect = pix.height / pix.width if pix.width else 1.0
        finally:
            pix = None

        stamped = 0
        for i in range(total):
            n = i + 1
            if n not in target_pages:
                continue
            page = doc.load_page(i)
            pw = page.rect.width
            ph = page.rect.height
            img_w = pw * scale
            img_h = img_w * aspect
            rect = _anchor_rect(anchor, pw, ph, img_w, img_h, ox, oy)
            kwargs = {"filename": str(image), "keep_proportion": True,
                      "overlay": True}
            if opacity < 1.0:
                try:
                    page.insert_image(rect, **kwargs, opacity=opacity)
                except TypeError:
                    page.insert_image(rect, **kwargs)
            else:
                page.insert_image(rect, **kwargs)
            stamped += 1

        if dry_run:
            click.echo(f"would stamp {stamped} pages with {image.name} → {target}")
            return

        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "pages_stamped": stamped, "image": str(image),
                   "at": anchor, "scale": scale})
    elif not quiet:
        click.echo(f"stamped {stamped} pages → {target}")
