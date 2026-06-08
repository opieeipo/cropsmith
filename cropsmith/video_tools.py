"""Video compression using the ffmpeg binary bundled by imageio-ffmpeg.

No system ffmpeg install required -- the binary ships inside the wheel, so the
packaged app is self-contained.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import CropsmithError


def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise CropsmithError(
            "imageio-ffmpeg is not installed. Run: pip install imageio-ffmpeg"
        ) from exc
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        raise CropsmithError(f"Could not locate the bundled ffmpeg binary: {exc}") from exc


def compress_video(input_video, output, crf: int = 28) -> Path:
    """Re-encode ``input_video`` to H.264 at the given CRF (0-51, lower = better)."""
    ffmpeg = _ffmpeg_exe()
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
        raise CropsmithError(f"ffmpeg failed:\n{result.stderr.strip()[-2000:]}")
    return Path(output)
