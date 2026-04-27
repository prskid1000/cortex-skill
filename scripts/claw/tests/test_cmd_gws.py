import pytest
from click.testing import CliRunner
from claw.__main__ import cli

# doc, drive, email
@pytest.mark.parametrize("noun", ["doc", "drive", "email"])
def test_gws_help(runner: CliRunner, noun):
    res = runner.invoke(cli, [noun, "--help"])
    assert res.exit_code == 0

@pytest.mark.parametrize("verb", ["send", "draft"])
def test_email_dry_run(runner: CliRunner, verb):
    res = runner.invoke(cli, ["email", verb, "--to", "x@y.z", "--subject", "s", "--body", "b", "--dry-run"])
    assert res.exit_code == 0

def test_drive_info_dry_run(runner: CliRunner):
    res = runner.invoke(cli, ["drive", "info", "FAKE_ID", "--dry-run"])
    assert res.exit_code == 0
