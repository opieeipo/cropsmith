"""Web page capture via Playwright (Chromium).

The Chromium browser is downloaded on demand the first time ``web-to-pdf`` runs,
so neither the standalone app nor a fresh pip install needs a manual
``playwright install`` step.
"""

from __future__ import annotations

import subprocess
import sys
from io import BytesIO
from pathlib import Path

from . import CropsmithError


def capture_region(url: str, region: tuple[int, int, int, int], output, progress=None) -> Path:
    """Render ``url`` in headless Chromium and save ``region`` as a PDF.

    ``region`` is ``(x, y, width, height)`` in page pixels.
    """
    progress = progress or (lambda _msg: None)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CropsmithError(
            "Playwright is not installed. Run: pip install playwright"
        ) from exc

    x, y, width, height = region
    output = Path(output)
    viewport_width = max(1280, x + width + 16)

    with sync_playwright() as pw:
        browser = _launch_chromium(pw, progress)
        try:
            page = browser.new_page(viewport={"width": viewport_width, "height": 1024})
            page.goto(url, wait_until="networkidle")
            png_bytes = page.screenshot(full_page=True)
        finally:
            browser.close()

    _png_region_to_pdf(png_bytes, region, output)
    return output


def _launch_chromium(pw, progress):
    """Launch Chromium, downloading the browser on first use if needed."""
    try:
        return pw.chromium.launch()
    except Exception as exc:  # noqa: BLE001
        if not _is_missing_browser(exc):
            raise CropsmithError(f"Could not launch Chromium: {exc}") from exc
    # Browser isn't installed yet -- fetch it once, then retry.
    _install_chromium(progress)
    try:
        return pw.chromium.launch()
    except Exception as exc:  # noqa: BLE001
        raise CropsmithError(
            "Chromium is still unavailable after download. "
            "Try running 'playwright install chromium' manually."
        ) from exc


def _is_missing_browser(exc) -> bool:
    message = str(exc).lower()
    return "executable doesn't exist" in message or "playwright install" in message


def _install_chromium(progress) -> None:
    progress("Downloading the Chromium browser (one-time, ~170 MB)...")
    last_error = None
    for cmd, env in _install_invocations():
        try:
            # Inherit stdout/stderr so the user sees Playwright's download progress.
            result = subprocess.run(cmd, env=env)
            if result.returncode == 0:
                progress("Browser ready.")
                return
            last_error = f"exit code {result.returncode}"
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
    raise CropsmithError(
        "Could not download the Chromium browser automatically "
        f"({last_error}). Run manually: playwright install chromium"
    )


def _install_invocations():
    """Yield ``(command, env)`` pairs to try for installing the browser.

    Frozen apps (PyInstaller) have no Python on PATH, so we invoke Playwright's
    bundled Node driver directly; in a normal environment we fall back to
    ``python -m playwright``.
    """
    invocations = []
    try:
        from playwright._impl._driver import compute_driver_executable, get_driver_env

        driver = compute_driver_executable()
        base = list(driver) if isinstance(driver, (list, tuple)) else [str(driver)]
        invocations.append((base + ["install", "chromium"], get_driver_env()))
    except Exception:  # noqa: BLE001 - private API; fall back below
        pass

    if not getattr(sys, "frozen", False):
        invocations.append(([sys.executable, "-m", "playwright", "install", "chromium"], None))

    return invocations


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
