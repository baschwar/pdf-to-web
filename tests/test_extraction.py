import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pdf_to_web.errors import PdfToWebError
from pdf_to_web.extraction import run_extraction
from pdf_to_web.project import create_project


class ExtractionTests(unittest.TestCase):
    def test_timeout_becomes_actionable_project_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            create_project(project)
            (project / "source" / "original.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
            with (
                patch(
                    "pdf_to_web.extraction.find_supported_java",
                    return_value=(Path("/usr/bin/java"), 17),
                ),
                patch("pdf_to_web.extraction.java_environment", return_value={}),
                patch(
                    "pdf_to_web.extraction.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(["java"], 1, output="partial"),
                ),
            ):
                with self.assertRaisesRegex(PdfToWebError, "exceeded the 1-second"):
                    run_extraction(project, timeout_seconds=1)
            data = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(data["extraction"]["status"], "failed")
            self.assertIn("timeout", data["extraction"]["last_error"])
            self.assertEqual(
                (project / "extraction" / "opendataloader.log").read_text(encoding="utf-8"),
                "partial",
            )


if __name__ == "__main__":
    unittest.main()
