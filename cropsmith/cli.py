"""Command-line entry point for Cropsmith.

Defines the ``cropsmith`` command and its sub-commands. Heavy / optional
dependencies are imported lazily inside each command so that ``cropsmith --help``
works even when a particular tool (Playwright, ffmpeg, Tesseract, ...) is missing.
"""

from __future__ import annotations

import functools
from pathlib import Path

import click

from . import CropsmithError, __version__


class AliasedGroup(click.Group):
    """A ``click.Group`` whose commands can be invoked by friendly aliases.

    This lets us expose intuitive primary names (``shrink-pdf``) while keeping
    older / alternative names (``compress-pdf``) working for muscle memory.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aliases: dict[str, str] = {}

    def command(self, *args, aliases=None, **kwargs):
        decorator = super().command(*args, **kwargs)
        if not aliases:
            return decorator

        def wrapper(fn):
            cmd = decorator(fn)
            for alias in aliases:
                self._aliases[alias] = cmd.name
            return cmd

        return wrapper

    def get_command(self, ctx, name):
        name = self._aliases.get(name, name)
        return super().get_command(ctx, name)

    def resolve_command(self, ctx, args):
        # Always report the canonical command name in usage/help output.
        _, cmd, rest = super().resolve_command(ctx, args)
        return cmd.name, cmd, rest


def _handle_errors(fn):
    """Turn :class:`CropsmithError` into a clean click message (no traceback)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except CropsmithError as exc:
            raise click.ClickException(str(exc)) from exc

    return wrapper


def _parse_box(box: str) -> tuple[int, int, int, int]:
    """Parse ``"x1,y1,x2,y2"`` into ``(x, y, width, height)``."""
    try:
        x1, y1, x2, y2 = (int(part.strip()) for part in box.split(","))
    except ValueError as exc:
        raise click.BadParameter(
            "must be four integers in the form 'x1,y1,x2,y2'", param_hint="--box"
        ) from exc
    x, y = min(x1, x2), min(y1, y2)
    width, height = abs(x2 - x1), abs(y2 - y1)
    if width == 0 or height == 0:
        raise click.BadParameter("region has zero width or height", param_hint="--box")
    return x, y, width, height


@click.group(cls=AliasedGroup)
@click.version_option(__version__, prog_name="cropsmith")
def main():
    """Cropsmith -- a friendly Swiss Army knife for documents and media."""


# --------------------------------------------------------------------------- #
# Web capture
# --------------------------------------------------------------------------- #
@main.command("web-to-pdf", aliases=["capture"])
@click.option("--url", required=True, help="Web page to capture.")
@click.option(
    "--box",
    required=True,
    help="Region to capture as 'x1,y1,x2,y2' in page pixels.",
)
@click.option(
    "--output", "-o", required=True,
    type=click.Path(dir_okay=False),
    help="Output PDF path.",
)
@_handle_errors
def web_to_pdf(url, box, output):
    """Save a region of a web page as a PDF."""
    from .capture import capture_region

    region = _parse_box(box)
    capture_region(url, region, output, progress=lambda msg: click.echo(msg))
    click.echo(f"Saved {output}")


# --------------------------------------------------------------------------- #
# PDF compression
# --------------------------------------------------------------------------- #
@main.command("shrink-pdf", aliases=["compress-pdf"])
@click.argument("input_pdf", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(dir_okay=False))
@click.option(
    "--level",
    type=click.Choice(["screen", "ebook", "printer", "prepress"]),
    default="screen",
    show_default=True,
    help="Quality preset (screen = smallest, prepress = highest quality).",
)
@_handle_errors
def shrink_pdf(input_pdf, output, level):
    """Reduce the file size of a PDF."""
    from .pdf_tools import compress_pdf

    compress_pdf(input_pdf, output, level)
    click.echo(f"Saved {output}")


# --------------------------------------------------------------------------- #
# Combine PDFs
# --------------------------------------------------------------------------- #
@main.command("merge-pdf", aliases=["combine", "merge"])
@click.argument("inputs", nargs=-1, required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(dir_okay=False))
@_handle_errors
def merge_pdf(inputs, output):
    """Combine multiple PDFs into a single file."""
    from .pdf_tools import combine_pdfs

    combine_pdfs(list(inputs), output)
    click.echo(f"Merged {len(inputs)} files into {output}")


# --------------------------------------------------------------------------- #
# PDF -> Word
# --------------------------------------------------------------------------- #
@main.command("pdf-to-word", aliases=["pdf2docx", "pdf-to-docx"])
@click.argument("input_pdf", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(dir_okay=False))
@_handle_errors
def pdf_to_word(input_pdf, output):
    """Convert a PDF into an editable Word (.docx) document."""
    from .pdf_tools import pdf_to_docx

    pdf_to_docx(input_pdf, output)
    click.echo(f"Saved {output}")


# --------------------------------------------------------------------------- #
# Video compression
# --------------------------------------------------------------------------- #
@main.command("shrink-video", aliases=["compress-video"])
@click.argument("input_video", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(dir_okay=False))
@click.option(
    "--crf",
    type=click.IntRange(0, 51),
    default=28,
    show_default=True,
    help="Quality: lower = better/larger (18 great, 28 good, 51 tiny).",
)
@_handle_errors
def shrink_video(input_video, output, crf):
    """Reduce the file size of a video."""
    from .video_tools import compress_video

    compress_video(input_video, output, crf)
    click.echo(f"Saved {output}")


# --------------------------------------------------------------------------- #
# OCR
# --------------------------------------------------------------------------- #
@main.command("extract-text", aliases=["ocr"])
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(dir_okay=False))
@_handle_errors
def extract_text(input_file, output):
    """Extract text from an image or scanned PDF."""
    from .ocr import run_ocr

    text = run_ocr(input_file)
    Path(output).write_text(text, encoding="utf-8")
    click.echo(f"Saved {output}")


# --------------------------------------------------------------------------- #
# Interactive screen-region page capture
# --------------------------------------------------------------------------- #
@main.command("capture-pages", aliases=["scan", "page-turner"])
@click.option("--output", "-o", required=True, type=click.Path(dir_okay=False))
@click.option("--box", default=None, help="x,y,w,h in logical screen pixels (skips the visual selector).")
@click.option("--key", default=None, help="Key that turns the page (e.g. right, space, pagedown).")
@click.option("--pages", type=int, default=None, help="How many pages to capture.")
@click.option("--interval", type=float, default=None, help="Seconds between page turns.")
@click.option(
    "--startup-delay", type=float, default=3.0, show_default=True,
    help="Seconds to focus your reader window before capture begins.",
)
@click.option("--ocr/--no-ocr", default=True, show_default=True, help="OCR each page into a searchable PDF.")
@_handle_errors
def capture_pages_cmd(output, box, key, pages, interval, startup_delay, ocr):
    """Capture a screen region across several pages into one (searchable) PDF.

    Draw a box over your reader, choose which key turns the page and how often,
    and Cropsmith captures each page and stitches them into a PDF.
    """
    from .screen_capture import capture_pages, parse_box_logical, select_region

    if box:
        region = parse_box_logical(box)
        logical_size = None
    else:
        click.echo("Drag a box around the area to capture (Esc to cancel)...")
        selection = select_region()
        if selection is None:
            raise click.ClickException("No region selected.")
        region, logical_size = selection
        click.echo(f"Region: x={region[0]} y={region[1]} w={region[2]} h={region[3]}")

    # Prompt for anything not supplied as a flag -- this is the interactive part.
    if key is None:
        key = click.prompt("Which key turns the page?", default="right")
    if pages is None:
        pages = click.prompt("How many pages?", default=10, type=int)
    if interval is None:
        interval = click.prompt("Seconds between page turns?", default=1.5, type=float)

    click.echo(
        f"\nFocus your reader window now. Capturing {pages} page(s), "
        f"pressing '{key}' every {interval}s.\n"
    )
    capture_pages(
        region, logical_size, output,
        key=key, pages=pages, interval=interval,
        startup_delay=startup_delay, ocr=ocr,
        progress=lambda msg: click.echo(msg),
    )
    click.echo(f"Saved {output}")


if __name__ == "__main__":
    main()
