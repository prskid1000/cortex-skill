"""claw pdf form — group aggregating form-related subcommands."""

from __future__ import annotations

import click

from claw.pdf.form_fill import form_fill as _form_fill
from claw.pdf.form_list import form_list as _form_list


@click.group(name="form", context_settings={"help_option_names": ["-h", "--help"]})
def form() -> None:
    """AcroForm operations — list, fill."""


form.add_command(_form_list, name="list")
form.add_command(_form_fill, name="fill")
