# PyInstaller spec for the standalone Cropsmith CLI.
# Build:  pyinstaller packaging/pyinstaller/cropsmith.spec --noconfirm
#
# Collects the packages that ship data files / native libs / bundled binaries so
# the result is fully self-contained (no system ffmpeg / tesseract / ghostscript).

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

datas, binaries, hiddenimports = [], [], []

# Packages whose *data* we genuinely need (ONNX models, the bundled ffmpeg
# binary, PyMuPDF/pdf2docx assets). These are small or essential.
for pkg in ("rapidocr_onnxruntime", "imageio_ffmpeg", "fitz", "pdf2docx"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Big native packages (onnxruntime ~400MB, opencv ~300MB as collected): collect
# their shared libs as BINARIES so PyInstaller strips + de-dupes them, instead of
# collect_all dumping unstripped copies into datas. Pull python modules via
# submodules, and any non-lib data files (excluding the libs we already took).
_LIB_GLOBS = ["**/*.dylib", "**/*.so", "**/*.so.*", "**/*.dll", "**/*.pyd"]
for pkg in ("onnxruntime",):
    try:
        binaries += collect_dynamic_libs(pkg)
        hiddenimports += collect_submodules(pkg)
        datas += collect_data_files(pkg, excludes=_LIB_GLOBS)
    except Exception:
        pass

# Lazily-imported packages: list as hidden imports so PyInstaller pulls them in
# via their built-in hooks (which de-dupe/strip correctly -- don't collect_all
# these or you get a second, unstripped copy). tkinter is imported lazily by the
# capture popup, so it must be named here to be bundled (its hook adds Tcl/Tk).
hiddenimports += ["cv2", "pynput", "mss", "PIL", "numpy",
                  "tkinter", "tkinter.filedialog"]

block_cipher = None

a = Analysis(
    ["entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter.test",
        # Heavy libraries no command needs -- keep them out of the bundle.
        "torch", "tensorflow", "matplotlib", "scipy", "pandas",
        "PyQt5", "PyQt6", "PySide2", "PySide6", "wx",
        "IPython", "jupyter", "notebook", "pytest", "sphinx", "tornado",
    ],
    cipher=block_cipher,
)
# Drop non-runtime packaging metadata (licenses, RECORD, WHEEL) -- saves ~100MB
# (numpy's dist-info licenses alone is 45MB). Keep METADATA / entry_points so
# runtime importlib.metadata lookups still work.
def _keep_datum(dest):
    path = str(dest).replace("\\", "/")
    if ".dist-info/" in path:
        return path.rsplit("/", 1)[-1] in ("METADATA", "entry_points.txt", "top_level.txt")
    return True


a.datas = [item for item in a.datas if _keep_datum(item[0])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cropsmith",
    console=True,
    strip=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    name="cropsmith",
)
