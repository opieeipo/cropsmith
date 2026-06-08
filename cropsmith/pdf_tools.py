"""PDF utilities: compress (PyMuPDF), combine (pypdf), convert to DOCX.

Compression uses PyMuPDF (bundled wheel) -- no Ghostscript install required.
"""

from __future__ import annotations

from pathlib import Path

from . import CropsmithError

# Quality presets map to the max DPI we allow embedded images to keep. Images
# above the target are downsampled; everything else is losslessly re-deflated.
_LEVEL_DPI = {
    "screen": 72,
    "ebook": 150,
    "printer": 300,
    "prepress": 0,  # 0 = no image downsampling, lossless optimise only
}


def compress_pdf(input_pdf, output, level: str = "screen") -> Path:
    """Shrink ``input_pdf`` into ``output``.

    Always applies lossless optimisation (deflate streams/fonts/images, garbage
    collect, clean). For ``screen``/``ebook``/``printer`` it additionally
    downsamples embedded images whose resolution exceeds the preset target.
    """
    import fitz

    target_dpi = _LEVEL_DPI.get(level, 72)
    doc = fitz.open(str(input_pdf))
    try:
        if target_dpi:
            _downsample_images(doc, target_dpi)
        doc.save(
            str(output),
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True,
        )
    finally:
        doc.close()
    return Path(output)


def _downsample_images(doc, target_dpi: int) -> None:
    """Re-encode images that are larger than ``target_dpi`` would need.

    Best-effort: any image we cannot safely rewrite is left untouched.
    """
    import fitz

    for page in doc:
        for info in page.get_images(full=True):
            xref = info[0]
            try:
                rects = page.get_image_rects(xref)
            except Exception:  # noqa: BLE001
                continue
            if not rects:
                continue
            display_in = max(rects[0].width, rects[0].height) / 72.0  # points -> inches
            if display_in <= 0:
                continue
            try:
                pix = fitz.Pixmap(doc, xref)
            except Exception:  # noqa: BLE001
                continue
            current_dpi = max(pix.width, pix.height) / display_in
            if current_dpi <= target_dpi * 1.1:
                continue
            scale = target_dpi / current_dpi
            new_w = max(1, int(pix.width * scale))
            new_h = max(1, int(pix.height * scale))
            try:
                if pix.alpha:  # drop alpha for JPEG
                    pix = fitz.Pixmap(pix, 0)
                shrunk = fitz.Pixmap(pix, new_w, new_h) if hasattr(fitz, "Pixmap") else pix
                page.replace_image(xref, pixmap=shrunk)
            except Exception:  # noqa: BLE001
                continue


def combine_pdfs(inputs, output) -> Path:
    """Merge ``inputs`` (in order) into a single ``output`` PDF."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    try:
        for pdf in inputs:
            writer.append(str(pdf))
        with open(output, "wb") as fh:
            writer.write(fh)
    finally:
        writer.close()
    return Path(output)


def pdf_to_docx(input_pdf, output) -> Path:
    """Convert ``input_pdf`` to an editable Word ``.docx`` document."""
    try:
        from pdf2docx import Converter
    except ImportError as exc:
        raise CropsmithError("pdf2docx is not installed. Run: pip install pdf2docx") from exc

    converter = Converter(str(input_pdf))
    try:
        converter.convert(str(output))
    finally:
        converter.close()
    return Path(output)
