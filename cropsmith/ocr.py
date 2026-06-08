"""OCR via RapidOCR (ONNX runtime) -- no system Tesseract required.

Everything here runs from pip-installed wheels (rapidocr-onnxruntime + PyMuPDF),
so the packaged app needs no external binaries. Two outputs are supported:

* plain text extraction (``run_ocr``)
* a searchable PDF -- the page image with an invisible OCR text layer on top
  (``searchable_pdf_from_images``), built with PyMuPDF.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from . import CropsmithError

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}

_engine = None


def _get_engine():
    """Lazily build the RapidOCR engine (loads ONNX models once)."""
    global _engine
    if _engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:
            raise CropsmithError(
                "rapidocr-onnxruntime is not installed. Run: pip install rapidocr-onnxruntime"
            ) from exc
        _engine = RapidOCR()
    return _engine


def _ocr_pil(pil_image):
    """Run OCR on a PIL image. Return a list of ``(box, text, score)``.

    ``box`` is four ``[x, y]`` points in pixel coordinates.
    """
    import numpy as np

    rgb = pil_image.convert("RGB")
    arr = np.asarray(rgb)[:, :, ::-1]  # RapidOCR expects BGR (cv2 convention)
    result, _ = _get_engine()(arr)
    return result or []


def _pdf_to_images(path, dpi=200):
    import fitz
    from PIL import Image

    images = []
    doc = fitz.open(path)
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            images.append(Image.open(BytesIO(pix.tobytes("png"))))
    finally:
        doc.close()
    return images


def run_ocr(input_file) -> str:
    """Return the text extracted from an image or PDF."""
    path = Path(input_file)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        images = _pdf_to_images(path)
    elif suffix in IMAGE_SUFFIXES:
        from PIL import Image

        images = [Image.open(path)]
    else:
        raise CropsmithError(
            f"Unsupported input type '{suffix}'. Provide an image "
            f"({', '.join(sorted(IMAGE_SUFFIXES))}) or a PDF."
        )

    pages = []
    for image in images:
        lines = [text for _box, text, _score in _ocr_pil(image)]
        pages.append("\n".join(lines))
    # Form-feed between pages so boundaries survive in the text file.
    return "\n\f\n".join(pages)


def searchable_pdf_from_images(images, dpi: int = 200) -> bytes:
    """Build a searchable PDF: each page is the image with an invisible OCR
    text layer positioned over the recognised words.
    """
    import fitz

    scale = 72.0 / dpi  # pixels -> PDF points
    doc = fitz.open()
    try:
        for pil_image in images:
            rgb = pil_image.convert("RGB")
            width_px, height_px = rgb.size
            page_w, page_h = width_px * scale, height_px * scale

            page = doc.new_page(width=page_w, height=page_h)
            buffer = BytesIO()
            rgb.save(buffer, format="JPEG", quality=80)
            page.insert_image(fitz.Rect(0, 0, page_w, page_h), stream=buffer.getvalue())

            for box, text, _score in _ocr_pil(rgb):
                xs = [point[0] for point in box]
                ys = [point[1] for point in box]
                x0, y1 = min(xs) * scale, max(ys) * scale
                box_height = max(1.0, (max(ys) - min(ys)) * scale)
                try:
                    page.insert_text(
                        (x0, y1 - box_height * 0.2),
                        text,
                        fontsize=box_height * 0.8,
                        render_mode=3,  # invisible -- selectable/searchable only
                    )
                except Exception:  # noqa: BLE001 - skip text we can't place
                    continue

        return doc.tobytes(garbage=3, deflate=True)
    finally:
        doc.close()
