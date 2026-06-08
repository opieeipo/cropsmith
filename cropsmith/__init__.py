"""Cropsmith -- a cross-platform Swiss Army knife for document and media manipulation."""

try:
    from importlib.metadata import version as _version

    __version__ = _version("cropsmith")  # single source of truth: pyproject.toml
except Exception:  # noqa: BLE001 - not installed (e.g. running from a raw checkout)
    __version__ = "0.3.0"


class CropsmithError(Exception):
    """Raised for expected, user-facing failures (missing tools, bad input, etc.).

    The CLI converts these into clean error messages instead of tracebacks.
    """
