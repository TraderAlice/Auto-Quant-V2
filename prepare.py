"""Prepare project-local OHLCV data for one Harness asset profile.

Usage:
    uv run prepare.py
    uv run prepare.py --profile us-equities --source-dir /path/to/ohlcv
    uv run prepare.py --list-profiles

Crypto profiles may delegate downloading to Freqtrade.  Other profiles use a
deliberately boring local import contract: one CSV, Parquet, or Feather file
per ``BASE_QUOTE-timeframe`` combination.  No Broker account is involved.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from autoquant.data import (
    DataCoverage,
    DataValidationError,
    expected_candle_paths,
    import_profile_data,
    inspect_profile_data,
    migrate_legacy_crypto_data,
)
from autoquant.profiles import AssetProfile, ManifestError, load_manifest


PROJECT_DIR = Path(__file__).parent.resolve()
USER_DATA = PROJECT_DIR / "user_data"
CONFIG = PROJECT_DIR / "config.json"
MANIFEST = PROJECT_DIR / "harness.json"


def _coverage_matches_timerange(
    coverages: list[DataCoverage],
    profile: AssetProfile,
) -> bool:
    start_text, end_text = profile.timerange.split("-", 1)
    required_start = pd.Timestamp(start_text, tz="UTC") if start_text else None
    required_end = pd.Timestamp(end_text, tz="UTC") if end_text else None
    grace = pd.Timedelta(days=7)
    for coverage in coverages:
        if required_start is not None and coverage.start > required_start + grace:
            return False
        if required_end is not None and coverage.end < required_end - grace:
            return False
    return True


def data_exists(profile: AssetProfile) -> bool:
    try:
        coverages = inspect_profile_data(PROJECT_DIR, profile)
    except (DataValidationError, OSError):
        return False
    return _coverage_matches_timerange(coverages, profile)


def _check_freqtrade_environment() -> None:
    try:
        import talib  # noqa: F401
    except ImportError:
        print(
            "ERROR: TA-Lib is not installed.\n\n"
            "Two install paths (see README.md for full detail):\n"
            "  1. Native: `brew install ta-lib` then `uv sync`\n"
            "  2. Docker fallback: use the Freqtrade image with TA-Lib built in.\n",
            file=sys.stderr,
        )
        raise SystemExit(1)


def download_with_freqtrade(profile: AssetProfile) -> None:
    _check_freqtrade_environment()
    from freqtrade.commands.data_commands import start_download_data

    data_dir = profile.data_dir(PROJECT_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    args = {
        "config": [str(CONFIG)],
        "user_data_dir": str(USER_DATA),
        "datadir": str(data_dir),
        "exchange": profile.venue,
        "pairs": list(profile.pairs),
        "timeframes": list(profile.timeframes),
        "timerange": profile.timerange,
        "dataformat_ohlcv": profile.data_format,
        "dataformat_trades": "feather",
        "download_trades": False,
        "trading_mode": profile.trading_mode,
        "prepend_data": True,
        "erase": False,
        "include_inactive_pairs": False,
        "new_pairs_days": 30,
    }
    start_download_data(args)


def _print_coverage(profile: AssetProfile, coverages: list[DataCoverage]) -> None:
    starts = [coverage.start for coverage in coverages]
    ends = [coverage.end for coverage in coverages]
    rows = sum(coverage.rows for coverage in coverages)
    print(
        f"Ready: {profile.id} — {len(coverages)} files, {rows:,} candles, "
        f"{min(starts).date()}..{max(ends).date()}"
    )
    print(f"Data:  {profile.data_dir(PROJECT_DIR)}")


def _print_local_import_help(profile: AssetProfile) -> None:
    print(
        f"No complete local dataset found for profile {profile.id!r}.\n"
        "Pass --source-dir containing one file per pair/timeframe. Supported "
        "formats: .csv, .parquet, .feather.\n\n"
        "Expected destination files:"
    )
    for path in expected_candle_paths(PROJECT_DIR, profile):
        print(f"  {path.relative_to(PROJECT_DIR)}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        help="asset profile id (default: manifest default or AUTOQUANT_PROFILE)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="import matching CSV/Parquet/Feather OHLCV files from this directory",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="list configured asset profiles and exit",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate existing local data without importing or downloading",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = load_manifest(MANIFEST)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.list_profiles:
        for profile_id, profile in manifest.profiles.items():
            marker = "*" if profile_id == manifest.default_profile else " "
            print(
                f"{marker} {profile_id}: {profile.asset_class} @ {profile.venue}, "
                f"{len(profile.pairs)} pairs, {profile.market_clock}"
            )
        return 0

    try:
        profile = manifest.profile(args.profile)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.validate_only:
        try:
            coverages = inspect_profile_data(PROJECT_DIR, profile)
        except (DataValidationError, OSError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        if not _coverage_matches_timerange(coverages, profile):
            print(
                f"ERROR: profile {profile.id!r} data does not cover "
                f"{profile.timerange}",
                file=sys.stderr,
            )
            return 1
        _print_coverage(profile, coverages)
        return 0

    # One-time compatibility migration from the v0.4 user_data/data layout.
    if profile.id == manifest.default_profile:
        migrated = migrate_legacy_crypto_data(PROJECT_DIR, profile)
        if migrated:
            print(
                f"Migrated {migrated} legacy candle files to "
                f"{profile.data_dir(PROJECT_DIR)}"
            )

    if args.source_dir is not None:
        try:
            coverages = import_profile_data(args.source_dir, PROJECT_DIR, profile)
        except (DataValidationError, OSError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_coverage(profile, coverages)
        return 0

    if data_exists(profile):
        _print_coverage(profile, inspect_profile_data(PROJECT_DIR, profile))
        return 0

    print(f"Profile:    {profile.id} ({profile.asset_class})")
    print(f"Venue:      {profile.venue}")
    print(f"Pairs:      {list(profile.pairs)}")
    print(f"Timeframes: {list(profile.timeframes)}")
    print(f"Timerange:  {profile.timerange}")
    print(f"Dest:       {profile.data_dir(PROJECT_DIR)}")
    print()

    if profile.data_provider == "freqtrade":
        download_with_freqtrade(profile)
        if not data_exists(profile):
            print(
                "ERROR: download appeared to succeed but the expected dataset "
                "is incomplete.",
                file=sys.stderr,
            )
            return 1
        _print_coverage(profile, inspect_profile_data(PROJECT_DIR, profile))
        return 0

    _print_local_import_help(profile)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
