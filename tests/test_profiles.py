from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoquant.profiles import ManifestError, load_manifest


PROJECT_DIR = Path(__file__).resolve().parents[1]


class HarnessManifestTests(unittest.TestCase):
    def test_repository_manifest_exposes_crypto_and_session_equities(self) -> None:
        manifest = load_manifest(PROJECT_DIR / "harness.json")

        self.assertEqual(manifest.default_profile, "crypto-majors")
        self.assertEqual(manifest.profile().asset_class, "crypto")
        self.assertEqual(
            manifest.interfaces.output_format,
            "autoquant-result-blocks",
        )
        self.assertIn("harness_version", manifest.interfaces.output_identity_fields)

        equities = manifest.profile("us-equities")
        self.assertEqual(equities.asset_class, "equity")
        self.assertTrue(equities.is_session_based)
        self.assertFalse(equities.fill_missing)
        self.assertEqual(equities.annualization_days, 252)
        self.assertTrue(
            equities.data_dir(PROJECT_DIR).is_relative_to(PROJECT_DIR.resolve())
        )

    def test_session_profile_cannot_enable_missing_candle_fill(self) -> None:
        raw = json.loads((PROJECT_DIR / "harness.json").read_text())
        raw["profiles"]["us-equities"]["data"]["fill_missing"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "harness.json"
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ManifestError, "must not fill"):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
