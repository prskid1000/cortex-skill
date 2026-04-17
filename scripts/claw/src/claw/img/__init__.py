"""claw img — image operations. See references/claw/img.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "resize":          ("claw.img.resize", "resize"),
    "fit":             ("claw.img.fit", "fit"),
    "pad":             ("claw.img.pad", "pad"),
    "thumb":           ("claw.img.thumb", "thumb"),
    "crop":            ("claw.img.crop", "crop"),
    "enhance":         ("claw.img.enhance", "enhance"),
    "sharpen":         ("claw.img.sharpen", "sharpen"),
    "composite":       ("claw.img.composite", "composite"),
    "watermark":       ("claw.img.watermark", "watermark"),
    "overlay":         ("claw.img.overlay", "overlay"),
    "convert":         ("claw.img.convert_", "convert_"),
    "to-jpeg":         ("claw.img.to_jpeg", "to_jpeg"),
    "to-webp":         ("claw.img.to_webp", "to_webp"),
    "exif":            ("claw.img.exif", "exif"),
    "rename":          ("claw.img.rename", "rename"),
    "batch":           ("claw.img.batch", "batch"),
    "gif-from-frames": ("claw.img.gif_from_frames", "gif_from_frames"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Image ops — resize, fit, thumb, enhance, sharpen, composite, exif, batch."""
