# Cropsmith

A cross-platform Swiss Army knife for document and media manipulation. Capture on-screen pages as searchable PDF, compress PDFs and videos, combine PDFs, convert PDF to DOCX, and run OCR -- all from a single CLI command available system-wide.

---

## Features

- **Page Capture** -- a crosshair + popup UI to box any on-screen reader, auto-turn pages, and OCR them into a searchable PDF (no embedded browser)
- **PDF Compression** -- reduce PDF file size while preserving quality
- **PDF Combine** -- merge multiple PDFs into a single file
- **PDF to Word** -- convert PDF files to editable Word (.docx) documents
- **Video Compression** -- compress video files using configurable quality settings
- **Text Extraction (OCR)** -- extract text from images or scanned PDFs
- **Right-click integration** -- run the file tools straight from the file manager's right-click menu (macOS + Windows)

---

## Commands at a glance

Cropsmith uses plain-language command names. Older/alternative names still work as aliases.

| Command | Aliases | What it does |
|---|---|---|
| `capture-pages` | `web-to-pdf`, `scan`, `page-turner` | Crosshair + popup to capture an on-screen reader across pages into a (searchable) PDF |
| `shrink-pdf` | `compress-pdf` | Compress a PDF |
| `merge-pdf` | `combine`, `merge` | Combine PDFs into one |
| `pdf-to-word` | `pdf2docx`, `pdf-to-docx` | Convert a PDF to Word (.docx) |
| `shrink-video` | `compress-video` | Compress a video |
| `extract-text` | `ocr` | Pull text out of an image or scanned PDF |

---

## Requirements

- Python 3.11+
- pip (comes with Python)
- Platform: macOS, Linux, or Windows (WSL recommended on Windows for full feature parity)

### System dependencies

**None.** Cropsmith is self-contained -- OCR, PDF compression and video
compression all run from bundled Python wheels (RapidOCR, PyMuPDF, and an ffmpeg
binary shipped inside `imageio-ffmpeg`). No `ffmpeg`, `tesseract` or
`ghostscript` install required.

The one extra: the **Page Capture** popup uses `tkinter`. It's included with the
standalone app and most Python builds, but Homebrew Python and minimal Linux
need it separately (`brew install python-tk@3.12`, `sudo apt install python3-tk`).

---

## Installation

### Download the app (no setup)

The easiest way -- no Python, no terminal, nothing to install. Grab the build for
your OS from the [latest release](https://github.com/opieeipo/cropsmith/releases/latest):

| OS | Download |
|---|---|
| macOS | `Cropsmith-macos.zip` -- unzip and run |
| Windows | `Cropsmith-windows.zip` -- unzip and run |
| Linux | `Cropsmith-linux.zip` -- unzip and run |

These bundles include everything (Python runtime + all engines). Nothing else to
install. Polished installers (`.dmg` / `.exe` / `.AppImage`) and right-click menu
integration are on the [roadmap](docs/ROADMAP.md).

---

### For developers (pipx / pip)

```bash
pipx install cropsmith          # once published to PyPI; works on macOS/Linux/Windows
```

See [`packaging/`](packaging/) for details.

---

### From source

### 1. Clone the repo

```bash
git clone https://github.com/youruser/cropsmith.git
cd cropsmith
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install the package in editable mode

This is the key step that makes `cropsmith` callable from anywhere without activating the venv manually:

```bash
pip install -e .
```

### 4. Verify

```bash
cropsmith --help
```

---

## Usage

### Capture pages from your screen (interactive)

You open the page in your own browser/reader; Cropsmith captures it -- there's no
embedded browser. Run:

```bash
cropsmith capture-pages          # alias: cropsmith web-to-pdf
```

A popup opens with a **crosshair region picker** and fields for the page-turn
key, number of pages, interval and output file. Pick the region, set the
options, click **Start Capture**, focus your reader window, and Cropsmith grabs
each page -- auto-pressing the key to turn pages -- and OCRs them into one
searchable PDF.

For scripting, skip the popup by passing the region and settings:

```bash
cropsmith capture-pages -o book.pdf --box 200,150,900,1200 --key right --pages 40 --interval 1.2
```

On macOS, grant your terminal **Screen Recording** and **Accessibility**
permissions (System Settings > Privacy & Security) the first time.

---

### Shrink (compress) a PDF

```bash
cropsmith shrink-pdf input.pdf --output compressed.pdf --level screen
```

Levels: `screen` (smallest), `ebook`, `printer`, `prepress` (highest quality)

---

### Merge PDFs

```bash
cropsmith merge-pdf file1.pdf file2.pdf file3.pdf --output combined.pdf
```

---

### PDF to Word

```bash
cropsmith pdf-to-word input.pdf --output output.docx
```

---

### Shrink (compress) a video

```bash
cropsmith shrink-video input.mp4 --output compressed.mp4 --crf 28
```

CRF range: 18 (high quality) to 51 (smallest file). Default: 28.

---

### Extract text (OCR)

Extract text from an image or scanned PDF:

```bash
cropsmith extract-text input.png --output extracted.txt
cropsmith extract-text scanned.pdf --output extracted.txt
```

---

## Right-click menu (macOS & Windows)

Add Cropsmith's file tools to your file manager's right-click menu:

```bash
cropsmith install-menu      # cropsmith uninstall-menu to remove
```

Then right-click a file:

| File | Actions |
|---|---|
| PDF | Shrink PDF, PDF → Word, Extract Text |
| Image | Extract Text |
| Video | Compress Video |
| Folder | Merge PDFs (every PDF in the folder → `merged.pdf`) |

Output is written next to the source (`foo-min.pdf`, `foo.docx`, `foo.txt`,
`foo-compressed.mp4`). Actions are scoped by file type, so PDF tools only show
on PDFs.

- **macOS** -- Finder > Quick Actions. Shows a notification when done. (Merge:
  select multiple PDFs.)
- **Windows** -- right-click a file directly (Windows 10) or under "Show more
  options" (Windows 11). Per-user, no admin. (Merge: right-click a folder, or
  inside it, to merge every PDF in that folder.)
- **Linux** -- on the [roadmap](docs/ROADMAP.md) (varies by desktop environment).

> The interactive `capture-pages` tool stays CLI-launched (it's a popup, not a
> file action).

---

## How the global command works

Cropsmith uses a `pyproject.toml` entry point to register the CLI command at install time:

```toml
[project.scripts]
cropsmith = "cropsmith.cli:main"
```

When you run `pip install -e .` inside your virtual environment, pip writes a `cropsmith` executable into the venv's `bin/` (or `Scripts/` on Windows) directory. If that venv is active or its bin path is on your `PATH`, you can call `cropsmith` from any directory.

For a permanent global install without activating the venv each time, use `pipx`:

```bash
pipx install .
```

`pipx` manages an isolated environment automatically and puts the command on your system PATH permanently.

---

## Project structure

```
cropsmith/
    cropsmith/
        __init__.py
        cli.py              # Entry point, command parsing, friendly aliases
        screen_capture.py   # Page Capture: crosshair picker + popup + grab
        pdf_tools.py        # Compress, combine, convert PDF
        video_tools.py      # Video compression via ffmpeg
        ocr.py              # OCR via Tesseract (+ PyMuPDF for PDFs)
    pyproject.toml
    README.md
```

---

## pyproject.toml (starter)

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cropsmith"
version = "0.1.0"
description = "Swiss Army knife for document and media manipulation"
requires-python = ">=3.11"
dependencies = [
    "pypdf",
    "pdf2docx",
    "rapidocr-onnxruntime",
    "imageio-ffmpeg",
    "Pillow",
    "PyMuPDF",
    "click",
    "mss",
    "pynput",
]

[project.scripts]
cropsmith = "cropsmith.cli:main"
```

---

## Recommended global install workflow (any platform)

```bash
# Install pipx if you don't have it
pip install pipx
pipx ensurepath

# Install cropsmith globally
cd /path/to/cropsmith
pipx install .

# Now callable from anywhere, no venv activation needed
cropsmith --help
```

---

## Platform notes

| Platform | Status | Notes |
|---|---|---|
| macOS | Full support | No system deps -- everything is bundled |
| Linux | Full support | No system deps -- everything is bundled |
| Windows | Full support | No system deps -- everything is bundled |

---

## License

MIT
