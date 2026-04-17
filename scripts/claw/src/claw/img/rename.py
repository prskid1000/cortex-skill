"""claw img rename — EXIF-driven template rename with collision handling."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, common_output_options, die, emit_json,
)


DEFAULT_PATTERNS = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.tif", "*.tiff", "*.heic",
                    "*.nef", "*.cr2", "*.cr3", "*.arw", "*.dng", "*.raf", "*.orf")

_TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(?::([^{}]+))?\}")


def _parse_exif_datetime(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


def _gather_exif(path: Path) -> dict:
    from PIL import Image, ExifTags
    img = Image.open(path)
    exif = img.getexif()
    out: dict = {"Width": img.width, "Height": img.height}
    for tag_id, value in exif.items():
        tag = ExifTags.TAGS.get(tag_id, str(tag_id))
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", errors="replace")
            except Exception:
                value = repr(value)
        out[tag] = value
    ifd = exif.get_ifd(0x8769) if hasattr(exif, "get_ifd") else {}
    for tag_id, value in (ifd or {}).items():
        tag = ExifTags.TAGS.get(tag_id, str(tag_id))
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", errors="replace")
            except Exception:
                value = repr(value)
        out.setdefault(tag, value)
    return out


def _get_token(name: str, meta: dict, src: Path, seq: int) -> object | None:
    if name == "seq":
        return seq
    if name == "ext":
        return src.suffix.lstrip(".").lower()
    if name == "Camera":
        return meta.get("Make") or meta.get("Model")
    if name == "Model":
        return meta.get("Model")
    if name in ("CreateDate", "DateTimeOriginal", "DateTime", "DateTimeDigitized"):
        raw = (meta.get("DateTimeOriginal") or meta.get("CreateDate")
               or meta.get("DateTimeDigitized") or meta.get("DateTime"))
        dt = _parse_exif_datetime(raw) if isinstance(raw, str) else None
        if dt is not None:
            return dt
        try:
            stat = src.stat()
            return datetime.fromtimestamp(stat.st_mtime)
        except OSError:
            return None
    if name in meta:
        return meta[name]
    return None


def _sanitize(part: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._\-/\\ ]+", "_", part).strip().strip(".")
    return clean or "unnamed"


def _render_template(template: str, meta: dict, src: Path, seq: int) -> str:
    def repl(m: re.Match) -> str:
        name = m.group(1)
        fmt = m.group(2)
        val = _get_token(name, meta, src, seq)
        if val is None:
            return ""
        if isinstance(val, datetime):
            return val.strftime(fmt) if fmt else val.strftime("%Y%m%d_%H%M%S")
        if fmt and isinstance(val, (int, float)):
            try:
                return format(val, fmt)
            except (ValueError, TypeError):
                return str(val)
        if fmt and isinstance(val, str):
            try:
                return format(val, fmt)
            except (ValueError, TypeError):
                return val
        return str(val)

    rendered = _TOKEN_RE.sub(repl, template)
    parts = rendered.replace("\\", "/").split("/")
    return "/".join(_sanitize(p) for p in parts if p != "")


def _resolve_collision(dst: Path, reserved: set[Path]) -> Path:
    if not dst.exists() and dst not in reserved:
        return dst
    stem = dst.stem
    suffix = dst.suffix
    n = 2
    while True:
        candidate = dst.with_name(f"{stem}-{n}{suffix}")
        if not candidate.exists() and candidate not in reserved:
            return candidate
        n += 1


@click.command(name="rename")
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option("--template", required=True,
              help="e.g. '{CreateDate:%Y%m%d}_{Camera}_{seq:03}.{ext}'")
@click.option("--recursive", is_flag=True, help="Recurse into subdirectories.")
@click.option("--pattern", default=None, help="Glob pattern (default: common image exts).")
@click.option("--lowercase-ext", is_flag=True, help="Force extension to lowercase.")
@common_output_options
def rename(target: Path, template: str, recursive: bool, pattern: str | None,
           lowercase_ext: bool,
           force: bool, backup: bool, as_json: bool, dry_run: bool,
           quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Rename files under <target> by an EXIF-driven template."""
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        die("Pillow not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[img]'", as_json=as_json)

    files: list[Path] = []
    if target.is_file():
        files = [target]
    else:
        patterns = [pattern] if pattern else list(DEFAULT_PATTERNS)
        for pat in patterns:
            files.extend(target.rglob(pat) if recursive else target.glob(pat))
        files = [f for f in sorted(set(files)) if f.is_file()]

    plan: list[dict] = []
    reserved: set[Path] = set()
    for seq, src in enumerate(files, start=1):
        try:
            meta = _gather_exif(src)
        except Exception as e:
            plan.append({"src": str(src), "error": f"exif read failed: {e}"})
            continue
        rendered = _render_template(template, meta, src, seq)
        if not rendered:
            plan.append({"src": str(src), "error": "template rendered empty"})
            continue
        dst = (src.parent / rendered).resolve() if not Path(rendered).is_absolute() \
            else Path(rendered)
        if lowercase_ext:
            dst = dst.with_suffix(dst.suffix.lower())
        if dst == src:
            plan.append({"src": str(src), "dst": str(dst), "skipped": "same-name"})
            continue
        dst = _resolve_collision(dst, reserved)
        reserved.add(dst)
        plan.append({"src": str(src), "dst": str(dst)})

    if dry_run:
        if as_json:
            emit_json({"count": len(plan), "items": plan})
        else:
            for rec in plan:
                if "error" in rec:
                    click.echo(f"SKIP {rec['src']}: {rec['error']}")
                elif "skipped" in rec:
                    click.echo(f"SKIP {rec['src']} ({rec['skipped']})")
                else:
                    click.echo(f"{rec['src']} -> {rec['dst']}")
        return

    renamed = 0
    errors: list[dict] = []
    for rec in plan:
        if "error" in rec or "skipped" in rec:
            continue
        src = Path(rec["src"])
        dst = Path(rec["dst"])
        try:
            if mkdir:
                dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and not force:
                errors.append({"src": str(src), "error": f"{dst} exists (pass --force)"})
                continue
            if backup and dst.exists():
                import shutil
                shutil.copy2(dst, dst.with_suffix(dst.suffix + ".bak"))
            src.replace(dst)
            renamed += 1
        except Exception as e:
            errors.append({"src": str(src), "error": str(e)})

    if as_json:
        emit_json({"renamed": renamed, "total": len(plan),
                   "items": plan, "errors": errors})
    elif not quiet:
        click.echo(f"renamed {renamed}/{len(plan)} file(s)")
        for err in errors:
            click.echo(f"error: {err['src']}: {err['error']}", err=True)
