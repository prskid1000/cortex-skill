"""claw email forward — forward an existing message to new recipients."""

from __future__ import annotations

import base64
import json
import sys
from email import message_from_bytes
from email.message import EmailMessage

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run, read_text

from claw.email._mime import _parse_addrs, build_message, to_raw_b64


def _fetch_raw(msg_id: str) -> EmailMessage:
    proc = gws_run("gmail", "users", "messages", "get",
                   "--params", json.dumps({
                       "userId": "me", "id": msg_id, "format": "raw",
                   }))
    if proc.returncode != 0:
        raise RuntimeError(f"gws get failed: {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    raw = base64.urlsafe_b64decode(data["raw"] + "==")
    return message_from_bytes(raw, _class=EmailMessage), data.get("threadId", "")


@click.command(name="forward")
@click.argument("msg_id")
@click.option("--to", "to", multiple=True, required=True)
@click.option("--cc", multiple=True)
@click.option("--bcc", multiple=True)
@click.option("--body", "body_text", default=None)
@click.option("--body-file", default=None, type=click.Path(exists=True, dir_okay=False))
@click.option("--body-stdin", is_flag=True)
@click.option("--subject", default=None)
@click.option("--no-attachments", is_flag=True)
@click.option("--strip-html", is_flag=True)
@click.option("--attach", "attachments", multiple=True)
@common_output_options
def forward(msg_id, to, cc, bcc, body_text, body_file, body_stdin, subject,
            no_attachments, strip_html, attachments,
            force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Forward <msg-id> with an optional note."""
    if sum(bool(x) for x in (body_text, body_file, body_stdin)) != 1:
        die("exactly one of --body, --body-file, --body-stdin required",
            code=EXIT_INPUT, as_json=as_json)

    if body_stdin:
        body = sys.stdin.read()
    elif body_file:
        body = read_text(body_file)
    else:
        body = body_text or ""

    try:
        parent, thread_id = _fetch_raw(msg_id)
    except (RuntimeError, FileNotFoundError) as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    parent_subject = parent.get("Subject", "")
    final_subject = subject or (parent_subject if parent_subject.lower().startswith("fwd:")
                                else f"Fwd: {parent_subject}")

    parent_plain = ""
    for part in parent.walk():
        if part.get_content_type() == "text/plain" and not part.is_attachment():
            try:
                parent_plain = part.get_content()
            except Exception:
                parent_plain = part.get_payload(decode=True).decode(errors="replace")
            break

    header_lines = (
        f"\n\n---------- Forwarded message ----------\n"
        f"From: {parent.get('From', '')}\n"
        f"Date: {parent.get('Date', '')}\n"
        f"Subject: {parent.get('Subject', '')}\n"
        f"To: {parent.get('To', '')}\n\n"
    )
    final_body = body + header_lines + parent_plain

    import os
    import tempfile

    with tempfile.TemporaryDirectory(prefix="claw-fwd-") as tmpdir:
        inherited: list[str] = []
        if not no_attachments:
            for part in parent.iter_attachments():
                name = part.get_filename() or "attachment.bin"
                path = os.path.join(tmpdir, name)
                with open(path, "wb") as f:
                    f.write(part.get_payload(decode=True) or b"")
                inherited.append(f"@{path}")

        try:
            msg = build_message(
                to=_parse_addrs(to), cc=_parse_addrs(cc), bcc=_parse_addrs(bcc),
                subject=final_subject, body=final_body,
                attachments=list(attachments) + inherited,
            )
        except (ValueError, FileNotFoundError) as e:
            die(str(e), code=EXIT_INPUT, as_json=as_json)

        raw_b64 = to_raw_b64(msg)

        if dry_run:
            if as_json:
                emit_json({"dry_run": True, "threadId": thread_id,
                           "headers": dict(msg.items()),
                           "inherited_attachments": len(inherited)})
            else:
                click.echo(msg.as_string()[:2048])
            return

        proc = gws_run("gmail", "users", "messages", "send",
                       "--params", json.dumps({"userId": "me"}),
                       "--json", json.dumps({"raw": raw_b64}))
        if proc.returncode != 0:
            die(f"gws send failed: {proc.stderr.strip()}", code=EXIT_SYSTEM, as_json=as_json)

        data = json.loads(proc.stdout)
        if as_json:
            emit_json(data)
        elif not quiet:
            click.echo(f"forwarded id={data.get('id', '?')}")
