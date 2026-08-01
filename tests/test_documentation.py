from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_repository_double_links_resolve(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_doc_links.py"],
            cwd=PROJECT_DIR,
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr or result.stdout,
        )
        self.assertIn("documentation double-links resolve", result.stdout)

    def test_release_document_ownership_does_not_drift(self) -> None:
        readme = (PROJECT_DIR / "README.md").read_text(encoding="utf-8")
        status = (PROJECT_DIR / "docs" / "STATUS.md").read_text(
            encoding="utf-8"
        )
        changelog = (PROJECT_DIR / "docs" / "CHANGELOG.md").read_text(
            encoding="utf-8"
        )
        agents = (PROJECT_DIR / "AGENTS.md").read_text(encoding="utf-8")

        self.assertEqual(readme.count("## Current release:"), 1)
        self.assertNotRegex(
            readme,
            re.compile(r"^#{2,}\s+`?v?0\.\d+\.\d+`?\s*$", re.MULTILINE),
        )
        self.assertNotRegex(
            status,
            re.compile(
                r"^#{2,}.*(?:v0\.\d+\.\d+|verification snapshot)",
                re.MULTILINE,
            ),
        )
        self.assertRegex(
            changelog,
            re.compile(r"^\| `v0\.9\.24` \|", re.MULTILINE),
        )
        self.assertIn("[[docs/CHANGELOG]]", agents[:5000])
        self.assertIn("[[docs/design/versioning-and-release]]", agents[:5000])


if __name__ == "__main__":
    unittest.main()
