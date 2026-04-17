"""claw img batch — op chain over a directory."""

from __future__ import annotations

import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, Geometry, common_output_options, die, emit_json, safe_write,
)


DEFAULT_PATTERNS = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.tif", "*.tiff", "*.heic")


def _apply_op(img, op: str):
    from PIL import Image, ImageFilter, ImageOps
    name, _, arg = op.partition(":")
    name = name.strip().lower()
    arg = arg.strip()
    if name == "resize":
        geo = Geometry.parse(arg)
        w, h = geo.apply_to(img.width, img.height)
        return img.resize((max(1, w), max(1, h)), Image.LANCZOS), "image"
    if name == "fit":
        w, h = (int(v) for v in arg.lower().split("x", 1))
        return ImageOps.fit(img, (w, h), method=Image.LANCZOS), "image"
    if name == "thumb":
        m = int(arg)
        copy = img.copy()
        copy.thumbnail((m, m), Image.LANCZOS, reducing_gap=3.0)
        return copy, "image"
    if name == "sharpen":
        if arg and "=" in arg:
            params = {k.strip(): float(v) for k, v in
                      (p.split("=", 1) for p in arg.split(",") if "=" in p)}
            r = params.get("radius", 2)
            a = params.get("amount", 150)
            t = params.get("threshold", 3)
        elif arg:
            parts = [float(p) for p in arg.split(",")]
            r, a, t = (parts + [2, 150, 3])[:3]
        else:
            r, a, t = 2, 150, 3
        return img.filter(ImageFilter.UnsharpMask(radius=r, percent=int(a), threshold=int(t))), "image"
    if name == "autocontrast":
        return ImageOps.autocontrast(img, cutoff=1), "image"
    if name == "rotate":
        spec = arg.lower()
        if spec in ("auto", ""):
            return ImageOps.exif_transpose(img), "image"
        try:
            angle = float(spec)
        except ValueError:
            raise click.UsageError(f"rotate: unknown arg {arg!r} (use auto|N)")
        return img.rotate(angle, expand=True, resample=Image.BICUBIC), "image"
    if name == "strip":
        data = list(img.getdata())
        clean = Image.new(img.mode, img.size)
        clean.putdata(data)
        return clean, "image"
    if name == "jpeg":
        q = int(arg) if arg else 85
        return img, ("JPEG", {"quality": q})
    if name == "webp":
        q = int(arg) if arg else 85
        return img, ("WEBP", {"quality": q})
    if name == "png":
        return img, ("PNG", {})
    raise click.UsageError(f"unknown op: {name}")


def _process_one(f: Path, op_list: list[str], directory: Path, out_dir: Path | None,
                 force: bool, backup: bool) -> dict:
    from PIL import Image
    save_fmt = None
    save_kwargs: dict = {}
    img = Image.open(f)
    for op in op_list:
        img, kind = _apply_op(img, op)
        if kind != "image":
            save_fmt, save_kwargs = kind
    if save_fmt is None:
        save_fmt = img.format or "PNG"
    target_ext = f".{save_fmt.lower()}" if save_fmt != "JPEG" else ".jpg"
    dst = (out_dir / f.relative_to(directory)).with_suffix(target_ext) \
        if out_dir else f.with_suffix(target_ext)
    buf = io.BytesIO()
    img.save(buf, format=save_fmt, **save_kwargs)
    safe_write(dst, lambda fp, b=buf: fp.write(b.getvalue()),
               force=force or (dst == f), backup=backup, mkdir=True)
    return {"src": str(f), "dst": str(dst)}


@click.command(name="batch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--op", "ops", required=True, help="Op chain: 'resize:1024x|strip|webp:85'")
@click.option("--out", "out_dir", default=None, type=click.Path(path_type=Path))
@click.option("--recursive", is_flag=True)
@click.option("--pattern", default=None, help="Glob pattern (default: common image exts).")
@click.option("--workers", type=int, default=1,
              help="Parallel workers (ThreadPoolExecutor).")
@click.option("--stream", is_flag=True, help="Emit one JSON line per file.")
@common_output_options
def batch(directory: Path, ops: str, out_dir: Path | None, recursive: bool,
          pattern: str | None, workers: int, stream: bool,
          force: bool, backup: bool, as_json: bool, dry_run: bool,
          quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Run an op chain on every image in <dir>."""
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        die("Pillow not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[img]'", as_json=as_json)

    patterns = [pattern] if pattern else list(DEFAULT_PATTERNS)
    files: list[Path] = []
    for pat in patterns:
        files.extend(directory.rglob(pat) if recursive else directory.glob(pat))
    files = [f for f in sorted(set(files)) if f.is_file()]

    op_list = [o.strip() for o in ops.split("|") if o.strip()]
    results: list[dict] = []

    if dry_run:
        for f in files:
            rec = {"src": str(f), "ops": op_list, "planned": True}
            results.append(rec)
            if stream:
                emit_json(rec)
        if not stream and as_json:
            emit_json({"count": len(results), "items": results})
        elif not stream and not quiet:
            click.echo(f"would process {len(results)} file(s)")
        return

    n_workers = max(1, workers if workers > 0 else (os.cpu_count() or 1))

    if n_workers == 1:
        for f in files:
            try:
                rec = _process_one(f, op_list, directory, out_dir, force, backup)
            except Exception as e:
                rec = {"src": str(f), "error": str(e)}
            results.append(rec)
            if stream:
                emit_json(rec)
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {ex.submit(_process_one, f, op_list, directory, out_dir,
                                 force, backup): f for f in files}
            for fut in as_completed(futures):
                src = futures[fut]
                try:
                    rec = fut.result()
                except Exception as e:
                    rec = {"src": str(src), "error": str(e)}
                results.append(rec)
                if stream:
                    emit_json(rec)

    errors = [r for r in results if "error" in r]
    if not stream and as_json:
        emit_json({"count": len(results), "errors": len(errors), "items": results})
    elif not stream and not quiet:
        click.echo(f"processed {len(results) - len(errors)}/{len(results)} file(s)")
        for err in errors:
            click.echo(f"error: {err['src']}: {err['error']}", err=True)
