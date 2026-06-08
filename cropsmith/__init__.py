"""Cropsmith -- a cross-platform Swiss Army knife for document and media manipulation."""

__version__ = "0.1.0"


class CropsmithError(Exception):
    """Raised for expected, user-facing failures (missing tools, bad input, etc.).

    The CLI converts these into clean error messages instead of tracebacks.
    """
