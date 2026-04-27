"""claw drive share — drive.permissions.create."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="share")
@click.argument("file_id")
@click.option("--user", default=None, help="Grant to this email.")
@click.option("--domain", default=None, help="Grant to this domain.")
@click.option("--anyone", is_flag=True, help="Grant to anyone-with-link.")
@click.option("--role",
              type=click.Choice(["reader", "commenter", "writer", "owner"]),
              required=True)
@click.option("--notify", is_flag=True)
@click.option("--message", "send_message", default=None, help="Custom email; implies --notify.")
@click.option("--transfer-ownership", is_flag=True, help="Required with --role owner.")
@common_output_options
def share(file_id, user, domain, anyone, role, notify, send_message,
          transfer_ownership,
          force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Grant Drive permission."""
    targets = sum(1 for x in (user, domain, anyone) if x)
    if targets != 1:
        die("exactly one of --user, --domain, --anyone required",
            code=EXIT_INPUT, as_json=as_json)

    if role == "owner" and not transfer_ownership:
        die("--role owner requires --transfer-ownership",
            code=EXIT_INPUT, hint="Drive refuses owner grants without it",
            as_json=as_json)

    body: dict = {"role": role}
    if user:
        body["type"] = "user"
        body["emailAddress"] = user
    elif domain:
        body["type"] = "domain"
        body["domain"] = domain
    else:
        body["type"] = "anyone"

    params: dict = {"fileId": file_id}
    if transfer_ownership:
        params["transferOwnership"] = True
    if notify or send_message:
        params["sendNotificationEmail"] = True
        if send_message:
            params["emailMessage"] = send_message
    else:
        params["sendNotificationEmail"] = False

    if dry_run:
        click.echo(f"would share file={file_id} params={params} body={body}")
        return

    try:
        proc = gws_run("drive", "permissions", "create",
                       "--params", json.dumps(params),
                       "--json", json.dumps(body))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws share failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    data = json.loads(proc.stdout)
    if as_json:
        emit_json({"file_id": file_id, "permission_id": data.get("id"),
                   "role": data.get("role"), "type": data.get("type")})
    elif not quiet:
        click.echo(f"granted {role} to {user or domain or 'anyone'} on {file_id} "
                   f"(perm={data.get('id', '?')})")
