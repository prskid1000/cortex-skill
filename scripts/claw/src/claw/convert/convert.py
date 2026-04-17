"""claw convert — pandoc-wrapped any↔any format translation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import click

from claw.common import (
    EXIT_SYSTEM, common_output_options, die, emit_json, require, run, safe_copy,
)


@click.command(name="convert",
               context_settings={"ignore_unknown_options": True,
                                 "allow_extra_args": True,
                                 "help_option_names": ["-h", "--help"]})
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(path_type=Path))
@click.option("--from", "fmt_from", default=None)
@click.option("--to", "fmt_to", default=None)
@click.option("--standalone", "-s", is_flag=True)
@click.option("--embed-resources", is_flag=True)
@click.option("--toc", is_flag=True)
@click.option("--toc-depth", type=int, default=None)
@click.option("--template", "template", default=None, type=click.Path(path_type=Path))
@click.option("--ref-doc", "ref_doc", default=None, type=click.Path(path_type=Path))
@click.option("--css", "css", default=None, type=click.Path(path_type=Path))
@click.option("--mathjax", is_flag=True)
@click.option("--katex", is_flag=True)
@click.option("--citeproc", is_flag=True)
@click.option("--bib", default=None, type=click.Path(path_type=Path))
@click.option("--csl", default=None, type=click.Path(path_type=Path))
@click.option("--engine", default=None,
              type=click.Choice(["xelatex", "lualatex", "pdflatex",
                                 "weasyprint", "typst", "tectonic"]))
@click.option("--highlight-style", default=None)
@click.option("--number-sections", is_flag=True)
@click.option("--metadata", "metadata", multiple=True)
@click.option("--variable", "variables", multiple=True)
@click.option("--defaults", "defaults_file", default=None, type=click.Path(path_type=Path),
              help="Forward a pandoc defaults YAML file.")
@common_output_options
@click.pass_context
def convert(ctx: click.Context, src: Path, dst: Path, fmt_from: str | None, fmt_to: str | None,
            standalone: bool, embed_resources: bool, toc: bool, toc_depth: int | None,
            template: Path | None, ref_doc: Path | None, css: Path | None,
            mathjax: bool, katex: bool, citeproc: bool,
            bib: Path | None, csl: Path | None, engine: str | None,
            highlight_style: str | None, number_sections: bool,
            metadata: tuple[str, ...], variables: tuple[str, ...],
            defaults_file: Path | None,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Convert <src> → <dst> via pandoc."""
    try:
        require("pandoc")
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, hint="winget install JohnMacFarlane.Pandoc", as_json=as_json)

    if bib and not citeproc:
        sys.stderr.write("warning: --bib passed without --citeproc (silently ignored by pandoc)\n")
    if mathjax and katex:
        die("--mathjax and --katex are mutually exclusive", code=2, as_json=as_json)
    if defaults_file and not defaults_file.exists():
        die(f"--defaults file not found: {defaults_file}", code=2, as_json=as_json)

    args: list[str] = [str(src)]
    if defaults_file: args += ["--defaults", str(defaults_file)]
    if fmt_from: args += ["--from", fmt_from]
    if fmt_to:   args += ["--to", fmt_to]
    if standalone:        args.append("--standalone")
    if embed_resources:   args.append("--embed-resources")
    if toc:               args.append("--toc")
    if toc_depth:         args.append(f"--toc-depth={toc_depth}")
    if template:          args.append(f"--template={template}")
    if ref_doc:           args.append(f"--reference-doc={ref_doc}")
    if css:               args.append(f"--css={css}")
    if mathjax:           args.append("--mathjax")
    if katex:             args.append("--katex")
    if citeproc:          args.append("--citeproc")
    if bib:               args.append(f"--bibliography={bib}")
    if csl:               args.append(f"--csl={csl}")
    if engine:            args.append(f"--pdf-engine={engine}")
    if highlight_style:   args.append(f"--highlight-style={highlight_style}")
    if number_sections:   args.append("--number-sections")
    for m in metadata:    args.append(f"--metadata={m}")
    for v in variables:   args.append(f"--variable={v}")
    args += list(ctx.args)

    with tempfile.TemporaryDirectory(prefix="claw-") as td:
        tmp = Path(td) / dst.name
        full = [*args, "-o", str(tmp)]
        if dry_run:
            click.echo("pandoc " + " ".join(full))
            return
        try:
            run("pandoc", *full)
        except Exception as e:
            die(f"pandoc failed: {e}", code=EXIT_SYSTEM, as_json=as_json)
        safe_copy(tmp, dst, force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"src": str(src), "dst": str(dst)})
    elif not quiet:
        click.echo(f"wrote {dst}")
