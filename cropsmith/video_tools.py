"""Video compression via ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import CropsmithError


def compress_video(input_video, output, crf: int = 28) -> Path:
    """Re-encode ``input_video`` to H.264 at the given CRF (0-51, lower = better)."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise CropsmithError(
            "ffmpeg not found. Install with: brew install ffmpeg  /  apt install ffmpeg"
        )

    cmd = [
        ffmpeg,
        "-y",
        "-i", str(input_video),
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", "medium",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # ffmpeg is verbose; keep the tail where the actual error usually is.
        raise CropsmithError(f"ffmpeg failed:\n{result.stderr.strip()[-2000:]}")
    return Path(output)
