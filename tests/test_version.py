from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from pdf_to_web import __version__


class VersionTests(unittest.TestCase):
    def test_runtime_version_matches_project_metadata(self) -> None:
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(__version__, metadata["project"]["version"])


if __name__ == "__main__":
    unittest.main()
