# Cropsmith

A cross-platform Swiss Army knife for document and media manipulation. Capture web page regions as PDF, compress PDFs and videos, combine PDFs, convert PDF to DOCX, and run OCR -- all from a single CLI command available system-wide.

---

## Features

- **Web Capture** -- screenshot a web page within a user-defined bounding box and export as PDF
- **PDF Compression** -- reduce PDF file size while preserving quality
- **PDF Combine** -- merge multiple PDFs into a single file
- **PDF to Word** -- convert PDF files to editable Word (.docx) documents
- **Video Compression** -- compress video files using configurable quality settings
- **Text Extraction (OCR)** -- extract text from images or scanned PDFs

---

## Commands at a glance

Cropsmith uses plain-language command names. Older/alternative names still work as aliases.

| Command | Aliases | What it does |
|---|---|---|
| `web-to-pdf` | `capture` | Save a web page region as a PDF |
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

### System dependencies (installed separately)

| Dependency | Purpose | Install |
|---|---|---|
| `ffmpeg` | Video compression | `brew install ffmpeg` / `apt install ffmpeg` |
| `tesseract` | OCR engine | `brew install tesseract` / `apt install tesseract-ocr` |
| `ghostscript` | PDF compression | `brew install ghostscript` / `apt install ghostscript` |
| `playwright` (Chromium) | Web capture | Installed automatically via setup |

---

## Installation

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

### 4. Install Playwright browser

```bash
playwright install chromium
```

### 5. Verify

```bash
cropsmith --help
```

---

## Usage

### Web capture to PDF

Capture a bounding box region of a web page and save as PDF.

```bash
cropsmith web-to-pdf --url "https://example.com" --box 100,200,800,600 --output capture.pdf
```

`--box` format is `x1,y1,x2,y2` in pixels relative to the rendered page.

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
cropsmith extract-text scanned.pdf --output extracted.txt --lang eng
```

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
        capture.py          # Web capture via Playwright
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
    "playwright",
    "pypdf",
    "pdf2docx",
    "pytesseract",
    "Pillow",
    "PyMuPDF",
    "click",
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
| macOS | Full support | Use Homebrew for system deps |
| Linux | Full support | Use apt/dnf for system deps |
| Windows (native) | Partial | ffmpeg, Tesseract and Ghostscript paths may need manual config |
| Windows (WSL2) | Full support | Recommended for Windows users |

---

## License

MIT
