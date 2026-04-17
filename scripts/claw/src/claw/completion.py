"""claw completion — shell completion script emitter.

Click ships with bash/zsh/fish completion built-in. PowerShell isn't yet
supported upstream, so we emit a minimal `Register-ArgumentCompleter` script
for pwsh that statically lists claw's top-level nouns and delegates to
`claw <noun> --help` for deeper completion.

See references/claw/completion.md.
"""

from __future__ import annotations

import os

import click


PWSH_TEMPLATE = r"""# claw PowerShell completion — source this from $PROFILE
# claude-claw skill
Register-ArgumentCompleter -Native -CommandName claw -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $tokens = @($commandAst.CommandElements | ForEach-Object { $_.Value })
    # Top-level nouns (kept in sync with NOUNS in claw/__main__.py)
    $nouns = @(
        'xlsx','docx','pptx','pdf','img','media','convert',
        'email','doc','sheet','web','html','xml','browser',
        'pipeline','doctor','completion','help'
    )

    if ($tokens.Count -le 2) {
        $nouns | Where-Object { $_ -like "$wordToComplete*" } |
            ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
        return
    }

    # Deeper: ask claw itself for subcommands via --help-all (fast, cached).
    $noun = $tokens[1]
    try {
        $help = & claw $noun --help 2>$null
        $verbs = $help | Select-String -Pattern '^\s+([\w-]+)\s+' -AllMatches |
                 ForEach-Object { $_.Matches } |
                 ForEach-Object { $_.Groups[1].Value } |
                 Sort-Object -Unique
        $verbs | Where-Object { $_ -like "$wordToComplete*" } |
            ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }
    } catch {}
}
"""


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "pwsh"]))
def completion(shell: str) -> None:
    """Emit a source-able completion script for the given shell.

    Examples:

        claw completion bash >> ~/.bashrc
        claw completion zsh  >> ~/.zshrc
        claw completion fish >  ~/.config/fish/completions/claw.fish
        claw completion pwsh >> $PROFILE
    """
    if shell == "pwsh":
        click.echo(PWSH_TEMPLATE)
        return

    os.environ["_CLAW_COMPLETE"] = f"{shell}_source"
    from claw.__main__ import cli  # noqa: PLC0415
    try:
        cli.main(prog_name="claw", args=[], standalone_mode=True)
    except SystemExit:
        pass
