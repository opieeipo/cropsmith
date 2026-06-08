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

    def __init__(self, key, title, verb, utis, multi=False, out_suffix="", out_ext=None):
        self.key = key            # stable id (used for filenames)
        self.title = title        # text shown in the menu
        self.verb = verb          # cropsmith subcommand
        self.utis = utis          # macOS uniform type identifiers to scope to
        self.multi = multi        # operate on all selected files at once
        self.out_suffix = out_suffix
        self.out_ext = out_ext    # None -> keep the input extension


# UTIs: com.adobe.pdf (PDF), public.image (images), public.movie (video).
ACTIONS = [
    MenuAction("shrink-pdf", "Cropsmith: Shrink PDF", "shrink-pdf",
               ["com.adobe.pdf"], out_suffix="-min", out_ext=".pdf"),
    MenuAction("pdf-to-word", "Cropsmith: PDF → Word", "pdf-to-word",
               ["com.adobe.pdf"], out_ext=".docx"),
    MenuAction("extract-text", "Cropsmith: Extract Text", "extract-text",
               ["com.adobe.pdf", "public.image"], out_ext=".txt"),
    MenuAction("shrink-video", "Cropsmith: Compress Video", "shrink-video",
               ["public.movie"], out_suffix="-compressed"),
    MenuAction("merge-pdf", "Cropsmith: Merge PDFs", "merge-pdf",
               ["com.adobe.pdf"], multi=True),
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


def install_menu(progress=None):
    progress = progress or (lambda _m: None)
    if sys.platform == "darwin":
        from . import macos

        return macos.install(cropsmith_executable(), progress)
    raise CropsmithError(
        f"Right-click menu integration isn't implemented for '{sys.platform}' yet "
        "(macOS only for now)."
    )


def uninstall_menu(progress=None):
    progress = progress or (lambda _m: None)
    if sys.platform == "darwin":
        from . import macos

        return macos.uninstall(progress)
    raise CropsmithError(f"No menu integration to remove on '{sys.platform}'.")
