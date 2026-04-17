"""claw media — video/audio operations. See references/claw/media.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "extract-audio": ("claw.media.extract_audio", "extract_audio"),
    "thumbnail":     ("claw.media.thumbnail", "thumbnail"),
    "gif":           ("claw.media.gif", "gif"),
    "trim":          ("claw.media.trim", "trim"),
    "compress":      ("claw.media.compress", "compress"),
    "scale":         ("claw.media.scale", "scale"),
    "concat":        ("claw.media.concat", "concat"),
    "burn-subs":     ("claw.media.burn_subs", "burn_subs"),
    "loudnorm":      ("claw.media.loudnorm", "loudnorm"),
    "speed":         ("claw.media.speed", "speed"),
    "fade":          ("claw.media.fade", "fade"),
    "crop-auto":     ("claw.media.crop_auto", "crop_auto"),
    "info":          ("claw.media.info", "info"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Video/audio — extract-audio, trim, compress, gif, loudnorm, burn-subs. Wraps ffmpeg."""
