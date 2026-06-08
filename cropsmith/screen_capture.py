"""Interactive on-screen page capture.

You open the page in your own browser/reader, then this tool:

1. shows a **crosshair region picker** (a translucent, click-through-feeling
   overlay that sits on top of your screen) to trace the capture box;
2. pops up a **settings dialog** (page-turn key, number of pages, interval,
   output file);
3. counts down so you can focus your window, then captures that region,
   auto-pressing the key to turn pages, and OCRs the frames into one searchable
   PDF.

No browser is embedded -- it captures whatever is on your screen.
"""

from __future__ import annotations

import time
from pathlib import Path

from . import CropsmithError

# Friendly key name -> pynput special key attribute name.
_SPECIAL_KEYS = {
    "right": "right", "left": "left", "up": "up", "down": "down",
    "space": "space", "enter": "enter", "return": "enter", "tab": "tab",
    "esc": "esc", "escape": "esc",
    "pagedown": "page_down", "page_down": "page_down",
    "pageup": "page_up", "page_up": "page_up",
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


def _new_tk():
    try:
        import tkinter as tk
    except ImportError as exc:  # pragma: no cover
        raise CropsmithError(
            "The page-capture popup needs tkinter, which isn't in this Python build:\n"
            "  macOS (Homebrew):  brew install python-tk@3.12\n"
            "  Debian/Ubuntu:     sudo apt install python3-tk\n"
            "  Fedora:            sudo dnf install python3-tkinter\n"
            "Or pass --box/--key/--pages/... to run headless without the popup."
        ) from exc
    return tk


# --------------------------------------------------------------------------- #
# Crosshair region picker -- a borderless, screen-sized, in-place overlay.
# Crucially NOT -fullscreen on macOS (that opens a separate Space and the
# overlay leaves your browser behind).
# --------------------------------------------------------------------------- #
def select_region():
    """Show the crosshair picker. Return ``((x, y, w, h), (sw, sh))`` or None."""
    tk = _new_tk()

    root = tk.Tk()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    try:
        root.overrideredirect(True)
    except tk.TclError:
        pass
    root.geometry(f"{sw}x{sh}+0+0")
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", 0.3)
    except tk.TclError:
        pass

    canvas = tk.Canvas(root, cursor="crosshair", bg="gray", highlightthickness=0,
                       width=sw, height=sh)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(sw // 2, 30, fill="#00ff99", font=("Helvetica", 16, "bold"),
                       text="Drag a box around the area to capture   •   Esc to cancel")

    state = {"box": None}
    drag = {"x": None, "y": None, "rect": None}
    guides = {"h": None, "v": None}

    def crosshair(event):
        if guides["h"] is None:
            guides["h"] = canvas.create_line(0, event.y, sw, event.y, fill="#ff4400")
            guides["v"] = canvas.create_line(event.x, 0, event.x, sh, fill="#ff4400")
        else:
            canvas.coords(guides["h"], 0, event.y, sw, event.y)
            canvas.coords(guides["v"], event.x, 0, event.x, sh)

    def on_press(event):
        drag["x"], drag["y"] = event.x, event.y
        if drag["rect"] is not None:
            canvas.delete(drag["rect"])
        drag["rect"] = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                               outline="#00ff99", width=2)

    def on_drag(event):
        crosshair(event)
        if drag["rect"] is not None:
            canvas.coords(drag["rect"], drag["x"], drag["y"], event.x, event.y)

    def finish(event):
        if drag["x"] is not None:
            left, top = min(drag["x"], event.x), min(drag["y"], event.y)
            w, h = abs(event.x - drag["x"]), abs(event.y - drag["y"])
            if w > 2 and h > 2:
                state["box"] = (left, top, w, h)
        root.destroy()

    def cancel(_event=None):
        state["box"] = None
        root.destroy()

    canvas.bind("<Motion>", crosshair)
    canvas.bind("<Button-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", finish)
    root.bind_all("<Escape>", cancel)
    root.lift()
    root.focus_force()
    root.mainloop()

    if state["box"] is None:
        return None
    return state["box"], (sw, sh)


# --------------------------------------------------------------------------- #
# Settings dialog (a normal window)
# --------------------------------------------------------------------------- #
def run_capture_gui(defaults: dict):
    """Pick the region, then collect settings. Return a settings dict or None."""
    selection = select_region()
    if selection is None:
        return None
    region, logical_size = selection
    settings = _settings_dialog(defaults, region)
    if settings is None:
        return None
    settings["region"] = region
    settings["logical_size"] = logical_size
    return settings


def _settings_dialog(defaults, region):
    tk = _new_tk()
    from tkinter import filedialog

    result = {"settings": None}
    root = tk.Tk()
    root.title("Cropsmith — Page Capture")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    pad = {"padx": 8, "pady": 4}

    x, y, w, h = region
    tk.Label(root, text=f"Region: {w}×{h} at ({x}, {y}).  Set the options, then Start.\n"
                        "You'll have a few seconds to focus your reader window.",
             justify="left").grid(row=0, column=0, columnspan=3, sticky="w", **pad)

    key_var = tk.StringVar(value=str(defaults.get("key", "right")))
    pages_var = tk.StringVar(value=str(defaults.get("pages", 10)))
    interval_var = tk.StringVar(value=str(defaults.get("interval", 1.5)))
    delay_var = tk.StringVar(value=str(defaults.get("startup_delay", 3.0)))
    ocr_var = tk.BooleanVar(value=bool(defaults.get("ocr", True)))
    out_var = tk.StringVar(value=str(defaults.get("output", "")))

    def field(r, label, var):
        tk.Label(root, text=label).grid(row=r, column=0, sticky="w", **pad)
        tk.Entry(root, textvariable=var, width=14).grid(row=r, column=1, sticky="w", **pad)

    field(1, "Key that turns the page:", key_var)
    field(2, "Number of pages:", pages_var)
    field(3, "Seconds between pages:", interval_var)
    field(4, "Seconds to get ready:", delay_var)
    tk.Checkbutton(root, text="Searchable PDF (OCR each page)", variable=ocr_var).grid(
        row=5, column=0, columnspan=2, sticky="w", **pad)

    tk.Label(root, text="Output PDF:").grid(row=6, column=0, sticky="w", **pad)
    tk.Entry(root, textvariable=out_var, width=28).grid(row=6, column=1, sticky="w", **pad)

    def browse():
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF", "*.pdf")])
        if path:
            out_var.set(path)
    tk.Button(root, text="Browse…", command=browse).grid(row=6, column=2, sticky="w", **pad)

    status = tk.Label(root, text="", fg="#b00")
    status.grid(row=7, column=0, columnspan=3, sticky="w", **pad)

    def start():
        try:
            s = {
                "key": key_var.get().strip() or "right",
                "pages": int(pages_var.get()),
                "interval": float(interval_var.get()),
                "startup_delay": float(delay_var.get()),
                "ocr": bool(ocr_var.get()),
                "output": out_var.get().strip(),
            }
        except ValueError:
            status.config(text="Pages must be a whole number; interval/delay must be numbers.")
            return
        if s["pages"] < 1:
            status.config(text="Number of pages must be at least 1.")
            return
        if not s["output"]:
            status.config(text="Choose an output PDF file.")
            return
        result["settings"] = s
        root.destroy()

    tk.Button(root, text="Start Capture", command=start, default="active").grid(
        row=8, column=1, sticky="e", **pad)
    tk.Button(root, text="Cancel", command=root.destroy).grid(row=8, column=2, sticky="w", **pad)
    root.lift()
    root.focus_force()
    root.mainloop()
    return result["settings"]


# --------------------------------------------------------------------------- #
# Capture
# --------------------------------------------------------------------------- #
def _resolve_key(name: str):
    from pynput.keyboard import Key

    attr = _SPECIAL_KEYS.get(name.strip().lower())
    return getattr(Key, attr) if attr is not None else name


def _press(controller, key) -> None:
    if isinstance(key, str) and len(key) != 1:
        controller.type(key)
    else:
        controller.press(key)
        controller.release(key)


def _build_controller():
    try:
        from pynput.keyboard import Controller
    except ImportError as exc:
        raise CropsmithError("pynput is not installed. Run: pip install pynput") from exc
    try:
        return Controller()
    except Exception as exc:  # noqa: BLE001
        raise CropsmithError(
            "Could not initialise keyboard control. On macOS grant your terminal "
            "Accessibility permission (System Settings > Privacy & Security > Accessibility)."
        ) from exc


def capture_pages(region_logical, logical_size, output, key="right", pages=10,
                  interval=1.5, startup_delay=3.0, ocr=True, progress=None) -> Path:
    """Capture ``region_logical`` ``pages`` times, pressing ``key`` between grabs."""
    progress = progress or (lambda _m: None)
    try:
        import mss
    except ImportError as exc:
        raise CropsmithError("mss is not installed. Run: pip install mss") from exc
    from PIL import Image

    controller = _build_controller()
    output = Path(output)
    pages = max(1, int(pages))

    with mss.mss() as sct:
        monitor = sct.monitors[1]
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

        for remaining in range(int(startup_delay), 0, -1):
            progress(f"Capturing in {remaining}... (focus your window)")
            time.sleep(1)

        key_obj = _resolve_key(key)
        frames = []
        for index in range(pages):
            shot = sct.grab(grab)
            frames.append(Image.frombytes("RGB", shot.size, shot.rgb))
            progress(f"Captured page {index + 1}/{pages}")
            if index < pages - 1:
                _press(controller, key_obj)
                time.sleep(interval)

    if ocr:
        progress("Running OCR and building searchable PDF...")
        from .ocr import searchable_pdf_from_images

        output.write_bytes(searchable_pdf_from_images(frames))
    else:
        frames[0].save(output, "PDF", save_all=True, append_images=frames[1:])

    return output
