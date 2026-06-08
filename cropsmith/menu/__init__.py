"""Right-click / context-menu integration.

Exposes ``install_menu`` / ``uninstall_menu`` which dispatch to a per-platform
implementation. Only the *file-based* verbs are exposed as menu actions
(``web-to-pdf`` and ``capture-pages`` are interactive, so they stay CLI-only).
"""

from __future__ import annotations

import os
import shutil
import sys

from .. import CropsmithError


class MenuAction:
    """One right-click action: which verb to run and how to name the output."""

    def __init__(self, key, title, verb, utis, exts, multi=False, out_suffix="", out_ext=None):
        self.key = key            # stable id (used for filenames / registry keys)
        self.title = title        # text shown in the menu
        self.verb = verb          # cropsmith subcommand
        self.utis = utis          # macOS uniform type identifiers to scope to
        self.exts = exts          # Windows file extensions to scope to
        self.multi = multi        # operate on all selected files at once
        self.out_suffix = out_suffix
        self.out_ext = out_ext    # None -> keep the input extension


_IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"]
_VIDEO_EXTS = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]

# UTIs: com.adobe.pdf (PDF), public.image (images), public.movie (video).
ACTIONS = [
    MenuAction("shrink-pdf", "Cropsmith: Shrink PDF", "shrink-pdf",
               ["com.adobe.pdf"], [".pdf"], out_suffix="-min", out_ext=".pdf"),
    MenuAction("pdf-to-word", "Cropsmith: PDF → Word", "pdf-to-word",
               ["com.adobe.pdf"], [".pdf"], out_ext=".docx"),
    MenuAction("extract-text", "Cropsmith: Extract Text", "extract-text",
               ["com.adobe.pdf", "public.image"], [".pdf"] + _IMAGE_EXTS, out_ext=".txt"),
    MenuAction("shrink-video", "Cropsmith: Compress Video", "shrink-video",
               ["public.movie"], _VIDEO_EXTS, out_suffix="-compressed"),
    MenuAction("merge-pdf", "Cropsmith: Merge PDFs", "merge-pdf",
               ["com.adobe.pdf"], [".pdf"], multi=True),
]


def cropsmith_executable() -> str:
    """Resolve an absolute path to the ``cropsmith`` executable.

    Menu actions run with a minimal environment (no user PATH), so we must embed
    the full path at install time rather than rely on PATH lookup at click time.
    """
    if getattr(sys, "frozen", False):
        return os.path.realpath(sys.executable)
    found = shutil.which("cropsmith")
    if found:
        return os.path.realpath(found)
    base = os.path.basename(sys.argv[0] or "")
    if base:
        found = shutil.which(base)
        if found:
            return os.path.realpath(found)
    return os.path.realpath(sys.argv[0])


def _platform_module():
    if sys.platform == "darwin":
        from . import macos

        return macos
    if sys.platform.startswith("win"):
        from . import windows

        return windows
    return None


def install_menu(progress=None):
    progress = progress or (lambda _m: None)
    mod = _platform_module()
    if mod is None:
        raise CropsmithError(
            f"Right-click menu integration isn't implemented for '{sys.platform}' yet "
            "(macOS and Windows only for now)."
        )
    return mod.install(cropsmith_executable(), progress)


def uninstall_menu(progress=None):
    progress = progress or (lambda _m: None)
    mod = _platform_module()
    if mod is None:
        raise CropsmithError(f"No menu integration to remove on '{sys.platform}'.")
    return mod.uninstall(progress)
