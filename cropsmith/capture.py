"""Web page capture via Playwright (Chromium)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from . import CropsmithError


def capture_region(url: str, region: tuple[int, int, int, int], output) -> Path:
    """Render ``url`` in headless Chromium and save ``region`` as a PDF.

    ``region`` is ``(x, y, width, height)`` in page pixels. We screenshot the
    full rendered page and crop, which is robust when the box extends past the
    visible viewport.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CropsmithError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        ) from exc

    x, y, width, height = region
    output = Path(output)
    # Render wide enough that the requested region is actually on the page.
    viewport_width = max(1280, x + width + 16)

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - surfaced as a friendly message
            raise CropsmithError(
                "Could not launch Chromium. Run: playwright install chromium"
            ) from exc
        try:
            page = browser.new_page(viewport={"width": viewport_width, "height": 1024})
            page.goto(url, wait_until="networkidle")
            png_bytes = page.screenshot(full_page=True)
        finally:
            browser.close()

    _png_region_to_pdf(png_bytes, region, output)
    return output


def _png_region_to_pdf(png_bytes: bytes, region: tuple[int, int, int, int], output: Path) -> None:
    from PIL import Image

    x, y, width, height = region
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    right = min(x + width, img.width)
    bottom = min(y + height, img.height)
    if x >= img.width or y >= img.height:
        raise CropsmithError(
            f"Capture box starts outside the rendered page (page is {img.width}x{img.height})."
        )
    cropped = img.crop((x, y, right, bottom))
    cropped.save(output, "PDF", resolution=100.0)
