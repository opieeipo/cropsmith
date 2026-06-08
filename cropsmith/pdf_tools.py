"""PDF utilities: compress (Ghostscript), combine (pypdf), convert to DOCX."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import CropsmithError


def _find_ghostscript() -> str | None:
    for name in ("gs", "gswin64c", "gswin32c"):
        path = shutil.which(name)
        if path:
            return path
    return None


def compress_pdf(input_pdf, output, level: str = "screen") -> Path:
    """Compress ``input_pdf`` into ``output`` using a Ghostscript quality preset."""
    gs = _find_ghostscript()
    if gs is None:
        raise CropsmithError(
            "Ghostscript ('gs') not found. Install with: "
            "brew install ghostscript  /  apt install ghostscript"
        )

    cmd = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{level}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output}",
        str(input_pdf),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise CropsmithError(f"Ghostscript failed:\n{result.stderr.strip()}")
    return Path(output)


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
