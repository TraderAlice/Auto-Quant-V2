from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
