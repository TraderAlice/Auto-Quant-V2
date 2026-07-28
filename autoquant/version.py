"""AutoQuant distribution version."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def current_version() -> str:
    """Return the installed AutoQuant version, or an honest unknown fallback."""

    try:
        return version("auto-quant")
    except PackageNotFoundError:
        return "0.0.0"
