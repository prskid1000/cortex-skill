"""claw xml validate — validate against XSD / RelaxNG (xml or compact) / DTD."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_SYSTEM, EXIT_USAGE, common_output_options, die, emit_json, run, which,
)


_TRANG_HINT = (
    "install trang: `winget install ThaiOpenSource.trang` "
    "or download from https://relaxng.org/jclark/trang.html"
)


def _compile_rnc_to_rng(rnc_path: Path, as_json: bool) -> Path:
    """Shell out to `trang` to convert an .rnc file to a temporary .rng file."""
    if which("trang") is None:
        die("RelaxNG Compact (.rnc) requires the `trang` tool which is not on PATH",
            code=EXIT_SYSTEM, hint=_TRANG_HINT, as_json=as_json)

    fd, tmp = tempfile.mkstemp(prefix="claw-rnc-", suffix=".rng")
    import os
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        run("trang", str(rnc_path), str(tmp_path))
    except FileNotFoundError:
        tmp_path.unlink(missing_ok=True)
        die("trang not found on PATH", code=EXIT_SYSTEM, hint=_TRANG_HINT, as_json=as_json)
    except subprocess.CalledProcessError as e:
        tmp_path.unlink(missing_ok=True)
        stderr = (e.stderr or "").strip()
        die(f"trang failed to compile {rnc_path}: {stderr or e}",
            code=EXIT_INPUT, as_json=as_json)
    return tmp_path


@click.command(name="validate")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--xsd", default=None, type=click.Path(exists=True, path_type=Path))
@click.option("--rng", default=None, type=click.Path(exists=True, path_type=Path))
@click.option("--rnc", default=None, type=click.Path(exists=True, path_type=Path))
@click.option("--dtd", default=None, type=click.Path(exists=True, path_type=Path))
@click.option("--all-errors", is_flag=True, help="Report every error (not first-fail).")
@common_output_options
def validate(src: Path, xsd: Path | None, rng: Path | None, rnc: Path | None,
             dtd: Path | None, all_errors: bool,
             force: bool, backup: bool, as_json: bool, dry_run: bool,
             quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Validate SRC against a schema. Exit 6 on validation failure."""
    try:
        from lxml import etree
    except ImportError:
        die("lxml not installed", code=EXIT_INPUT,
            hint="pip install 'claw[xml]'", as_json=as_json)

    schemas = [x for x in ((xsd, "xsd"), (rng, "rng"), (rnc, "rnc"), (dtd, "dtd")) if x[0]]
    if len(schemas) != 1:
        die("exactly one of --xsd / --rng / --rnc / --dtd is required",
            code=EXIT_USAGE, as_json=as_json)
    schema_path, kind = schemas[0]

    if dry_run:
        click.echo(f"would validate {src} against {kind} {schema_path}")
        return

    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
    try:
        doc = etree.parse(str(src), parser=parser)
    except etree.XMLSyntaxError as e:
        die(f"XML parse error: {e}", code=EXIT_INPUT, as_json=as_json)

    compiled_rng: Path | None = None
    try:
        if kind == "xsd":
            schema = etree.XMLSchema(etree.parse(str(schema_path), parser=parser))
        elif kind == "rng":
            schema = etree.RelaxNG(etree.parse(str(schema_path), parser=parser))
        elif kind == "rnc":
            compiled_rng = _compile_rnc_to_rng(schema_path, as_json)
            schema = etree.RelaxNG(etree.parse(str(compiled_rng), parser=parser))
        else:
            schema = etree.DTD(str(schema_path))
    except (etree.XMLSchemaParseError, etree.RelaxNGParseError,
            etree.DTDParseError, etree.XMLSyntaxError) as e:
        if compiled_rng is not None:
            compiled_rng.unlink(missing_ok=True)
        die(f"schema load error: {e}", code=EXIT_INPUT, as_json=as_json)

    try:
        valid = schema.validate(doc)
        errors = []
        if not valid:
            log = schema.error_log
            items = list(log) if all_errors else ([log[0]] if len(log) else [])
            for err in items:
                errors.append({
                    "line": err.line, "column": err.column,
                    "domain": err.domain_name, "type": err.type_name,
                    "message": err.message,
                })
    finally:
        if compiled_rng is not None:
            compiled_rng.unlink(missing_ok=True)

    if as_json:
        emit_json({"valid": valid, "errors": errors})
    elif valid:
        if not quiet:
            click.echo(f"valid: {src}")
    else:
        for e in errors:
            click.echo(f"{e['line']}:{e['column']} {e['message']}", err=True)

    if not valid:
        sys.exit(6)
