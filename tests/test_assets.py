import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from pdf_to_web.assets import extract_pdf_assets


class AssetExtractionTests(unittest.TestCase):
    def test_empty_pdf_writes_provenance_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            with source.open("wb") as stream:
                writer.write(stream)
            manifest = extract_pdf_assets(source, root / "assets" / "images")
            self.assertEqual(manifest["extraction_engine"], "pypdf")
            self.assertEqual(manifest["association_scope"], "source_page_only")
            self.assertEqual(manifest["asset_reference_count"], 0)
            self.assertTrue((root / "assets" / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
