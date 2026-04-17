"""claw pdf encrypt — password-protect a PDF with access flags."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


PERMS = ("print", "copy", "modify", "annotate", "fill-forms", "assemble", "print-high")


def _perm_map() -> dict[str, int]:
    """Resolve pypdf's UserAccessPermissions bits across versions.

    Newer pypdf (4.x+) exposes members like PRINT, EXTRACT, MODIFY, etc.
    Older pypdf used slightly different names. Fallback to raw PDF 1.7 bit values.
    """
    try:
        from pypdf.constants import UserAccessPermissions as P
    except ImportError:
        die("pypdf not installed; install: pip install 'claw[pdf]'")

    return {
        "print":      int(getattr(P, "PRINT", 4)),
        "copy":       int(getattr(P, "EXTRACT", getattr(P, "COPY", 16))),
        "modify":     int(getattr(P, "MODIFY", 8)),
        "annotate":   int(getattr(P, "ADD_OR_MODIFY", getattr(P, "ANNOTATE", 32))),
        "fill-forms": int(getattr(P, "FILL_FORM_FIELDS", 256)),
        "assemble":   int(getattr(P, "ASSEMBLE_DOC", getattr(P, "ASSEMBLE", 1024))),
        "print-high": int(getattr(P, "PRINT_TO_REPRESENTATION",
                                  getattr(P, "PRINT_HIGH_QUALITY", 2048))),
    }


def _all_allowed() -> int:
    """Bitmask with all user-relevant permission bits set.

    PDF 1.7: bits 1-2 are reserved (must be 0), bits 7-8 reserved (must be 1),
    bits 13-32 reserved. The canonical "allow everything" literal is 0xFFFFFFFC
    (all bits set except the two reserved-zero bits).
    """
    try:
        from pypdf.constants import UserAccessPermissions as P
        for name in ("all", "ALL"):
            fn = getattr(P, name, None)
            if callable(fn):
                return int(fn())
    except ImportError:
        pass
    return 0xFFFFFFFC


def _build_permissions(allow: str | None, deny: str | None) -> int:
    mapping = _perm_map()
    if allow:
        names = [x.strip() for x in allow.split(",") if x.strip()]
        flags = 0
        for n in names:
            if n not in mapping:
                die(f"unknown permission: {n}; valid: {', '.join(mapping)}")
            flags |= mapping[n]
        return flags
    if deny:
        names = [x.strip() for x in deny.split(",") if x.strip()]
        flags = _all_allowed()
        for n in names:
            if n not in mapping:
                die(f"unknown permission: {n}; valid: {', '.join(mapping)}")
            flags &= ~mapping[n]
        return flags
    return 0


@click.command(name="encrypt")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--password", "-p", required=True, help="User password.")
@click.option("--owner-password", default=None, help="Owner password (default = user).")
@click.option("--aes256", "algo", flag_value="AES-256", help="AES-256 (needs pycryptodome).")
@click.option("--aes128", "algo", flag_value="AES-128", default=True)
@click.option("--rc4-128", "algo", flag_value="RC4-128")
@click.option("--allow", default=None, help=f"CSV subset: {','.join(PERMS)}")
@click.option("--deny", default=None, help="CSV subset to deny.")
@click.option("-o", "--out", type=click.Path(path_type=Path), required=True)
@common_output_options
def encrypt(src: Path, password: str, owner_password: str | None, algo: str,
            allow: str | None, deny: str | None, out: Path,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Encrypt <SRC> with --password."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        die("pypdf not installed; install: pip install 'claw[pdf]'")

    if allow and deny:
        die("--allow and --deny are mutually exclusive", code=2)

    reader = PdfReader(str(src))
    writer = PdfWriter(clone_from=reader)
    perms = _build_permissions(allow, deny)

    kwargs = {"user_password": password,
              "owner_password": owner_password or password,
              "algorithm": algo,
              "permissions_flag": perms}

    try:
        writer.encrypt(**kwargs)
    except (ImportError, ModuleNotFoundError):
        die(f"{algo} requires pycryptodome; install: pip install 'claw[crypto]'")

    if dry_run:
        click.echo(f"would encrypt {src} with {algo} → {out}")
        return

    safe_write(out, lambda f: writer.write(f), force=force, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(out), "algorithm": algo,
                   "allow": allow, "deny": deny})
    elif not quiet:
        click.echo(f"encrypted → {out} ({algo})")
