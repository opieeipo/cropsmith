"""OCR for images and scanned PDFs via Tesseract (pytesseract)."""

from __future__ import annotations

import shutil
from io import BytesIO
from pathlib import Path

from . import CropsmithError

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}


def run_ocr(input_file, lang: str = "eng") -> str:
    """Return the text extracted from an image or PDF via OCR."""
    input_file = Path(input_file)
    suffix = input_file.suffix.lower()

    try:
        import pytesseract
    except ImportError as exc:
        raise CropsmithError("pytesseract is not installed. Run: pip install pytesseract") from exc

    if shutil.which(pytesseract.pytesseract.tesseract_cmd) is None and shutil.which("tesseract") is None:
        raise CropsmithError(
            "Tesseract OCR engine not found. Install with: "
            "brew install tesseract  /  apt install tesseract-ocr"
        )

    if suffix == ".pdf":
        return _ocr_pdf(input_file, lang)
    if suffix in IMAGE_SUFFIXES:
        return _ocr_image(input_file, lang)
    raise CropsmithError(
        f"Unsupported input type '{suffix}'. Provide an image ({', '.join(sorted(IMAGE_SUFFIXES))}) or a PDF."
    )


def _ocr_image(path: Path, lang: str) -> str:
    import pytesseract
    from PIL import Image

    with Image.open(path) as img:
        return pytesseract.image_to_string(img, lang=lang)


def _ocr_pdf(path: Path, lang: str) -> str:
    import pytesseract
    from PIL import Image

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise CropsmithError(
            "PyMuPDF is required to OCR PDFs. Run: pip install PyMuPDF"
        ) from exc

    pages: list[str] = []
    doc = fitz.open(path)
    try:
        for page in doc:
            pixmap = page.get_pixmap(dpi=200)
            with Image.open(BytesIO(pixmap.tobytes("png"))) as img:
                pages.append(pytesseract.image_to_string(img, lang=lang))
    finally:
        doc.close()
    # Separate pages with a form-feed so page boundaries survive in the text file.
    return "\n\f\n".join(pages)
