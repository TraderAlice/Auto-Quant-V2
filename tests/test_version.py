from __future__ import annotations

import re
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

from autoquant.runs import harness_identity
from autoquant.version import current_version


PROJECT_DIR = Path(__file__).resolve().parents[1]


class VersionContractTests(unittest.TestCase):
    def test_openalice_readme_package_cli_and_runs_agree(self) -> None:
        package_version = tomllib.loads(
            (PROJECT_DIR / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["version"]
        readme = (PROJECT_DIR / "README.md").read_text(encoding="utf-8")
        match = re.match(
            r"\A---\s*\n.*?^version:\s*[\"']?([^\"'\s]+)[\"']?\s*$.*?^---\s*$",
            readme,
            flags=re.MULTILINE | re.DOTALL,
        )

        self.assertIsNotNone(match, "README must start with version frontmatter")
        self.assertEqual(match.group(1), package_version)
        self.assertEqual(current_version(), package_version)
        self.assertEqual(harness_identity()["version"], package_version)

        cli = subprocess.run(
            [sys.executable, "-m", "autoquant", "--version"],
            cwd=PROJECT_DIR,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertEqual(cli.stdout.strip(), f"aq {package_version}")


if __name__ == "__main__":
    unittest.main()
