"""Interactive screen-region capture with auto page-turning and OCR.

Flow:
    1. ``select_region`` shows a translucent fullscreen overlay; the user drags
       a box. The overlay is then **fully destroyed** -- nothing is drawn over
       the captured area, so the selection rectangle never appears in the output
       (this was the bug in the original ScreenRecorder.py).
    2. ``capture_pages`` grabs that region N times, pressing a key between grabs
       to turn the page, OCRs each frame into a searchable PDF page, and merges
       them into one file.
"""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path

from . import CropsmithError

# Friendly key name -> pynput special key attribute name.
_SPECIAL_KEYS = {
    "right": "right",
    "left": "left",
    "up": "up",
    "down": "down",
    "space": "space",
    "enter": "enter",
    "return": "enter",
    "tab": "tab",
    "esc": "esc",
    "escape": "esc",
    "pagedown": "page_down",
    "page_down": "page_down",
    "pageup": "page_up",
    "page_up": "page_up",
}


def parse_box_logical(box: str) -> tuple[int, int, int, int]:
    """Parse ``"x,y,w,h"`` (logical screen pixels) into a 4-tuple."""
    try:
        x, y, w, h = (int(part.strip()) for part in box.split(","))
    except ValueError as exc:
        raise CropsmithError("--box must be four integers: 'x,y,width,height'") from exc
    if w <= 0 or h <= 0:
        raise CropsmithError("--box width and height must be positive")
    return x, y, w, h


def select_region():
    """Show the selection overlay. Return ``((x, y, w, h), (screen_w, screen_h))``
    in logical pixels, or ``None`` if the user cancelled.
    """
    try:
        import tkinter as tk
    except ImportError as exc:  # pragma: no cover - tkinter ships with CPython
        raise CropsmithError(
            "tkinter is required for interactive selection. On Homebrew Python: brew install python-tk"
        ) from exc

    state = {"box": None}
    drag = {"x": None, "y": None, "rect": None}

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.attributes("-topmost", True)
    try:
        root.overrideredirect(True)
    except tk.TclError:
        pass

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    canvas = tk.Canvas(
        root, cursor="cross", bg="gray", highlightthickness=0,
        width=screen_w, height=screen_h,
    )
    canvas.pack(fill="both", expand=True)
    info = tk.Label(
        root, text="Drag to select the capture region   •   Esc to cancel",
        bg="#1a1a1a", fg="#00ff99", font=("Helvetica", 14, "bold"), padx=12, pady=8,
    )
    canvas.create_window(20, screen_h - 60, anchor="nw", window=info)

    def on_press(event):
        drag["x"], drag["y"] = event.x, event.y
        if drag["rect"] is not None:
            canvas.delete(drag["rect"])
        drag["rect"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#ff4400", width=3, dash=(6, 4)
        )

    def on_drag(event):
        if drag["rect"] is None:
            return
        canvas.coords(drag["rect"], drag["x"], drag["y"], event.x, event.y)
        left, top = min(drag["x"], event.x), min(drag["y"], event.y)
        width, height = abs(event.x - drag["x"]), abs(event.y - drag["y"])
        info.config(text=f"x={left} y={top}   w={width} h={height}   •   release to confirm")

    def on_release(event):
        if drag["x"] is None:
            return
        left, top = min(drag["x"], event.x), min(drag["y"], event.y)
        width, height = abs(event.x - drag["x"]), abs(event.y - drag["y"])
        if width > 2 and height > 2:
            state["box"] = (left, top, width, height)
        root.destroy()

    def cancel(_event=None):
        state["box"] = None
        root.destroy()

    canvas.bind("<Button-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", cancel)
    root.mainloop()

    if state["box"] is None:
        return None
    return state["box"], (screen_w, screen_h)


def _resolve_key(name: str):
    from pynput.keyboard import Key

    attr = _SPECIAL_KEYS.get(name.strip().lower())
    if attr is not None:
        return getattr(Key, attr)
    return name  # a literal character / string to type


def _press(controller, key) -> None:
    # `key` is either a pynput Key, a single char, or a multi-char string.
    if isinstance(key, str) and len(key) != 1:
        controller.type(key)
    else:
        controller.press(key)
        controller.release(key)


def capture_pages(
    region_logical: tuple[int, int, int, int],
    logical_size,
    output,
    key: str = "right",
    pages: int = 10,
    interval: float = 1.5,
    startup_delay: float = 3.0,
    lang: str = "eng",
    ocr: bool = True,
    progress=None,
) -> Path:
    """Capture ``region_logical`` ``pages`` times, turning the page with ``key``.

    ``logical_size`` is the ``(w, h)`` the region was measured against (used to
    rescale for Retina/HiDPI). Pass ``None`` to assume a 1:1 mapping.
    """
    try:
        import mss
    except ImportError as exc:
        raise CropsmithError("mss is not installed. Run: pip install mss") from exc
    from PIL import Image

    pytesseract = None
    if ocr:
        try:
            import pytesseract as _pt
        except ImportError as exc:
            raise CropsmithError("pytesseract is not installed. Run: pip install pytesseract") from exc
        import shutil

        if shutil.which(_pt.pytesseract.tesseract_cmd) is None and shutil.which("tesseract") is None:
            raise CropsmithError(
                "Tesseract OCR engine not found. Install: brew install tesseract / apt install tesseract-ocr"
            )
        pytesseract = _pt

    try:
        controller = _build_controller()
    except CropsmithError:
        raise

    output = Path(output)
    pages = max(1, int(pages))

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary physical monitor
        scale_x = scale_y = 1.0
        if logical_size:
            scale_x = monitor["width"] / logical_size[0]
            scale_y = monitor["height"] / logical_size[1]

        x, y, w, h = region_logical
        grab = {
            "left": monitor["left"] + int(round(x * scale_x)),
            "top": monitor["top"] + int(round(y * scale_y)),
            "width": int(round(w * scale_x)),
            "height": int(round(h * scale_y)),
        }

        # Countdown so the user can focus their reader window first.
        for remaining in range(int(startup_delay), 0, -1):
            if progress:
                progress(f"Capturing in {remaining}... (focus your reader window)")
            time.sleep(1)

        key_obj = _resolve_key(key)
        pdf_writer = None
        images = []
        if ocr:
            from pypdf import PdfWriter

            pdf_writer = PdfWriter()

        for index in range(pages):
            shot = sct.grab(grab)
            frame = Image.frombytes("RGB", shot.size, shot.rgb)
            if ocr:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(frame, extension="pdf", lang=lang)
                pdf_writer.append(BytesIO(pdf_bytes))
            else:
                images.append(frame)
            if progress:
                progress(f"Captured page {index + 1}/{pages}")
            if index < pages - 1:
                _press(controller, key_obj)
                time.sleep(interval)

        if ocr:
            with open(output, "wb") as fh:
                pdf_writer.write(fh)
            pdf_writer.close()
        else:
            images[0].save(output, "PDF", save_all=True, append_images=images[1:])

    return output


def _build_controller():
    try:
        from pynput.keyboard import Controller
    except ImportError as exc:
        raise CropsmithError("pynput is not installed. Run: pip install pynput") from exc
    try:
        return Controller()
    except Exception as exc:  # noqa: BLE001 - e.g. missing accessibility permission
        raise CropsmithError(
            "Could not initialise keyboard control. On macOS grant your terminal "
            "Accessibility permission (System Settings > Privacy & Security > Accessibility)."
        ) from exc
