"""claw pptx brand — inject logo / accent color / font across masters."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _normalize_hex(hex_color: str) -> str:
    h = hex_color.lstrip("#").upper()
    if len(h) not in (3, 6, 8):
        raise ValueError(f"bad hex color: {hex_color!r}")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return h[:6]


def _update_accent1(theme_xml, hex_color: str) -> bool:
    """Rewrite theme clrScheme/accent1 to the given RRGGBB hex. Returns True if changed."""
    from lxml import etree

    ns = {"a": A_NS}
    accents = theme_xml.findall(".//a:clrScheme/a:accent1", ns)
    if not accents:
        return False
    changed = False
    for accent in accents:
        for child in list(accent):
            accent.remove(child)
        srgb = etree.SubElement(accent, f"{{{A_NS}}}srgbClr")
        srgb.set("val", hex_color)
        changed = True
    return changed


def _update_fonts(theme_xml, font_name: str) -> bool:
    """Rewrite majorFont/minorFont Latin typefaces. Returns True if changed."""
    ns = {"a": A_NS}
    changed = False
    for tag in ("majorFont", "minorFont"):
        for fontset in theme_xml.findall(f".//a:fontScheme/a:{tag}", ns):
            latin = fontset.find("a:latin", ns)
            if latin is not None:
                latin.set("typeface", font_name)
                changed = True
    return changed


@click.command(name="brand")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--logo", "logo_path", default=None,
              type=click.Path(exists=True, path_type=Path),
              help="Image inserted bottom-right of every slide master.")
@click.option("--accent-color", "accent_color", default=None,
              help="#RRGGBB applied to every theme's accent1.")
@click.option("--accent", "accent_bar", default=None,
              help="Hex color for the accent bar; defaults to the primary brand hex "
                   "(i.e. --accent-color).")
@click.option("--font-name", "font_name", default=None,
              help="Typeface applied to every theme's major/minor Latin font.")
@click.option("--logo-size", "logo_size", default="1in,0.5in", show_default=True,
              help="w,h (in|cm|pt|emu) for the inserted logo.")
@click.option("--logo-at", "logo_at", default="tr",
              type=click.Choice(["tl", "tr", "bl", "br"], case_sensitive=False),
              help="Corner placement of the logo (default tr).")
@common_output_options
def brand(src: Path, logo_path: Path | None, accent_color: str | None,
          accent_bar: str | None,
          font_name: str | None, logo_size: str, logo_at: str,
          force: bool, backup: bool, as_json: bool, dry_run: bool,
          quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Bulk-apply brand elements (logo, accent color, fonts) across masters."""
    try:
        from pptx import Presentation
        from pptx.util import Cm, Emu, Inches, Pt
        from lxml import etree
    except ImportError:
        die("python-pptx (and lxml) not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    if not any([logo_path, accent_color, accent_bar, font_name]):
        die("pass at least one of --logo / --accent-color / --accent / --font-name",
            code=EXIT_INPUT, as_json=as_json)

    hex_color = None
    if accent_color:
        try:
            hex_color = _normalize_hex(accent_color)
        except ValueError as e:
            die(str(e), code=EXIT_INPUT, as_json=as_json)

    accent_bar_hex = None
    if accent_bar is not None:
        try:
            accent_bar_hex = _normalize_hex(accent_bar)
        except ValueError as e:
            die(str(e), code=EXIT_INPUT, as_json=as_json)
    elif hex_color is not None:
        accent_bar_hex = hex_color

    def _to_emu(spec: str):
        spec = spec.strip().lower()
        if spec.endswith("in"):
            return Inches(float(spec[:-2]))
        if spec.endswith("cm"):
            return Cm(float(spec[:-2]))
        if spec.endswith("pt"):
            return Pt(float(spec[:-2]))
        return Emu(int(spec))

    logo_w = logo_h = None
    if logo_path:
        try:
            ws_, hs_ = logo_size.split(",")
            logo_w, logo_h = _to_emu(ws_), _to_emu(hs_)
        except (ValueError, IndexError):
            die(f"invalid --logo-size: {logo_size!r}", code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would apply brand (logo={bool(logo_path)}, "
                   f"accent={hex_color}, font={font_name})")
        return

    prs = Presentation(str(src))

    logos_added = 0
    if logo_path:
        slide_w, slide_h = prs.slide_width, prs.slide_height
        margin = Inches(0.25)
        corner = logo_at.lower()
        if corner == "tl":
            left, top = margin, margin
        elif corner == "tr":
            left, top = slide_w - logo_w - margin, margin
        elif corner == "bl":
            left, top = margin, slide_h - logo_h - margin
        else:
            left, top = slide_w - logo_w - margin, slide_h - logo_h - margin
        for slide in prs.slides:
            slide.shapes.add_picture(str(logo_path), left, top,
                                     width=logo_w, height=logo_h)
            logos_added += 1

    accents_updated = 0
    fonts_updated = 0
    if hex_color or font_name:
        for master in prs.slide_masters:
            theme_part = None
            for rel in master.part.rels.values():
                if rel.reltype.endswith("/theme"):
                    theme_part = rel.target_part
                    break
            if theme_part is None:
                continue
            theme_xml = etree.fromstring(theme_part.blob)
            dirty = False
            if hex_color and _update_accent1(theme_xml, hex_color):
                accents_updated += 1
                dirty = True
            if font_name and _update_fonts(theme_xml, font_name):
                fonts_updated += 1
                dirty = True
            if dirty:
                theme_part.blob = etree.tostring(
                    theme_xml, xml_declaration=True,
                    encoding="UTF-8", standalone=True,
                )

    def _save(f):
        prs.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({
            "path": str(src),
            "logos_added": logos_added,
            "accents_updated": accents_updated,
            "fonts_updated": fonts_updated,
            "accent": hex_color,
            "accent_bar": accent_bar_hex,
            "logo_at": logo_at.lower() if logo_path else None,
            "font": font_name,
        })
    elif not quiet:
        bits = []
        if logos_added:
            bits.append(f"{logos_added} logo(s)")
        if accents_updated:
            bits.append(f"accent on {accents_updated} master(s)")
        if fonts_updated:
            bits.append(f"font on {fonts_updated} master(s)")
        click.echo("applied brand: " + ", ".join(bits or ["no-op"]))
