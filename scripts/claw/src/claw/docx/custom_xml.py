"""claw docx custom-xml attach — embed a custom XML part in the document."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_copy


CUSTOM_XML_CT = "application/xml"
CUSTOM_XML_REL_TYPE = ("http://schemas.openxmlformats.org/officeDocument/"
                       "2006/relationships/customXml")


@click.group(name="custom-xml")
def custom_xml() -> None:
    """Attach / inspect custom XML parts on the OPC package."""


@custom_xml.command(name="attach")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--part", "part_path", required=True,
              type=click.Path(exists=True, path_type=Path),
              help="Path to the XML file to embed.")
@click.option("--id", "part_id", default=None,
              help="Optional custom part identifier (default: auto-numbered).")
@common_output_options
def custom_xml_attach(src: Path, part_path: Path, part_id: str | None,
                      force: bool, backup: bool, as_json: bool, dry_run: bool,
                      quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Attach a custom XML part to the docx package."""
    try:
        from lxml import etree  # noqa: F401
    except ImportError:
        die("lxml not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    xml_bytes = part_path.read_bytes()

    if dry_run:
        click.echo(f"would attach {part_path} to {src}")
        return

    with zipfile.ZipFile(src) as zf:
        existing = zf.namelist()

    n = 1
    while f"customXml/item{n}.xml" in existing:
        n += 1
    target_name = f"customXml/item{n}.xml"
    rels_name = f"customXml/_rels/item{n}.xml.rels"

    tmp_dir = Path(tempfile.mkdtemp(prefix="claw-docx-cx-"))
    try:
        staged = tmp_dir / src.name
        with zipfile.ZipFile(src) as zin, zipfile.ZipFile(staged, "w",
                                                         zipfile.ZIP_DEFLATED) as zout:
            ct_updated = False
            doc_rels_updated = False
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    data = _patch_content_types(data, target_name)
                    ct_updated = True
                elif item.filename == "word/_rels/document.xml.rels":
                    data = _patch_doc_rels(data, target_name, part_id)
                    doc_rels_updated = True
                zout.writestr(item, data)
            if not ct_updated:
                die("[Content_Types].xml missing from package",
                    code=EXIT_INPUT, as_json=as_json)
            if not doc_rels_updated:
                die("word/_rels/document.xml.rels missing",
                    code=EXIT_INPUT, as_json=as_json)
            zout.writestr(target_name, xml_bytes)
            zout.writestr(rels_name, _empty_rels())

        if src.exists() and not force:
            die(f"{src} exists (pass --force)",
                code=EXIT_INPUT, as_json=as_json)
        safe_copy(staged, src, force=True, backup=backup, mkdir=mkdir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if as_json:
        emit_json({"path": str(src), "part": target_name, "id": part_id})
    elif not quiet:
        click.echo(f"attached {target_name}")


def _patch_content_types(data: bytes, part_name: str) -> bytes:
    from lxml import etree

    root = etree.fromstring(data)
    ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    override = etree.SubElement(root, f"{{{ns}}}Override")
    override.set("PartName", "/" + part_name)
    override.set("ContentType", CUSTOM_XML_CT)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                          standalone=True)


def _patch_doc_rels(data: bytes, part_name: str, part_id: str | None) -> bytes:
    from lxml import etree

    root = etree.fromstring(data)
    ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    ids = [child.get("Id") for child in root]
    if part_id and part_id in ids:
        raise click.ClickException(f"--id {part_id} already exists")
    if not part_id:
        n = len(ids) + 1
        while f"rId{n}" in ids:
            n += 1
        part_id = f"rId{n}"

    rel = etree.SubElement(root, f"{{{ns}}}Relationship")
    rel.set("Id", part_id)
    rel.set("Type", CUSTOM_XML_REL_TYPE)
    rel.set("Target", "../" + part_name)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                          standalone=True)


def _empty_rels() -> bytes:
    return (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/'
            b'package/2006/relationships"/>')
