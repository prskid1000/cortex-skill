"""claw pptx reorder — reorder slides by 1-based index list."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.command(name="reorder")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--order", required=True,
              help="Comma-separated 1-based slide indices, e.g. 3,1,2,4.")
@click.option("--start-at", "start_at", default=1, type=int, show_default=True,
              help="Treat --order as N-based (1 by default).")
@common_output_options
def reorder(src: Path, order: str, start_at: int,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Reorder slides by a comma-separated index list.

    python-pptx has no stable slide-move API; manipulate sldIdLst XML directly.
    """
    try:
        from pptx import Presentation
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    try:
        indices = [int(x.strip()) - start_at for x in order.split(",") if x.strip()]
    except ValueError:
        die(f"invalid --order: {order!r}", code=EXIT_INPUT, as_json=as_json)

    if not indices:
        die("--order must contain at least one index", code=EXIT_INPUT, as_json=as_json)

    prs = Presentation(str(src))
    n = len(prs.slides)

    if any(i < 0 or i >= n for i in indices):
        die(f"index out of range (deck has {n} slides)",
            code=EXIT_INPUT, as_json=as_json)
    if len(set(indices)) != len(indices):
        die("--order contains duplicates", code=EXIT_INPUT, as_json=as_json)
    if len(indices) != n:
        die(f"--order must list all {n} slides (got {len(indices)})",
            code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would reorder {n} slides -> {[i + start_at for i in indices]}")
        return

    sldIdLst = prs.slides._sldIdLst
    items = list(sldIdLst)
    for item in items:
        sldIdLst.remove(item)
    for i in indices:
        sldIdLst.append(items[i])

    def _save(f):
        prs.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "order": [i + start_at for i in indices],
                   "slide_count": n})
    elif not quiet:
        click.echo(f"reordered {n} slides")
