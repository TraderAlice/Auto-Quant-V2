"""Auto-Quant harness primitives.

The autonomous research loop still lives in ``program.md``.  This package
contains the stable, non-strategy parts that make the loop portable across
asset profiles.
"""

from .profiles import AssetProfile, HarnessInterfaces, HarnessManifest, load_manifest

__all__ = [
    "AssetProfile",
    "HarnessInterfaces",
    "HarnessManifest",
    "load_manifest",
]
