# PyInstaller spec for the standalone Cropsmith CLI.
# Build:  pyinstaller packaging/pyinstaller/cropsmith.spec --noconfirm
#
# Collects the packages that ship data files / native libs / bundled binaries so
# the result is fully self-contained (no system ffmpeg / tesseract / ghostscript).

from PyInstaller.utils.hooks import collect_all, collect_data_files

datas, binaries, hiddenimports = [], [], []

for pkg in (
    "rapidocr_onnxruntime",   # ONNX models + config yaml
    "onnxruntime",            # native runtime libs
    "imageio_ffmpeg",         # bundled ffmpeg binary
    "fitz",                   # PyMuPDF native libs
    "cv2",                    # opencv (pulled by rapidocr / pdf2docx)
    "pdf2docx",
):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        # Package may be importable under a different name; skip gracefully.
        pass

# pynput / mss backends are imported lazily; make sure they're discoverable.
hiddenimports += ["pynput", "mss", "PIL", "numpy"]

block_cipher = None

a = Analysis(
    ["entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter.test", "torch", "tensorflow"],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cropsmith",
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="cropsmith",
)
