import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pdf_to_web.project import create_project, import_pdf, load_project


class ProjectTests(unittest.TestCase):
    @mock.patch("pdf_to_web.pdf_analysis.analyze_pdf", return_value={"classification": "TEXT PDF", "page_count": 1, "ocr_status": "not_required"})
    def test_import_preserves_source_filename(self, _analyze):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            source = root / "Policy Document.pdf"
            source.write_bytes(b"%PDF-1.4\n%%EOF")
            create_project(project)

            import_pdf(project, source)

            self.assertTrue((project / "source" / source.name).is_file())
            self.assertEqual(load_project(project)["source"]["path"], f"source/{source.name}")

    @mock.patch("pdf_to_web.pdf_analysis.analyze_pdf", return_value={"classification": "TEXT PDF", "page_count": 1, "ocr_status": "not_required"})
    def test_import_uses_readable_collision_suffix_without_overwriting(self, _analyze):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            source = root / "Policy.pdf"
            source.write_bytes(b"new")
            create_project(project)
            existing = project / "source" / "Policy.pdf"
            existing.write_bytes(b"existing")

            import_pdf(project, source)

            self.assertEqual(existing.read_bytes(), b"existing")
            self.assertEqual((project / "source" / "Policy-2.pdf").read_bytes(), b"new")
            state = load_project(project)
            self.assertEqual(state["source"]["path"], "source/Policy-2.pdf")
            self.assertEqual(state["source"]["original_filename"], "Policy.pdf")


if __name__ == "__main__":
    unittest.main()
