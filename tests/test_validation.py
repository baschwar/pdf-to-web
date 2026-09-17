import json
import unittest
from pathlib import Path

from pdf_to_web.exporters.gutenberg import render_document as render_gutenberg
from pdf_to_web.exporters.html import render_document as render_html
from pdf_to_web.exporters.wxr import render_wxr
from pdf_to_web.validation import validate_gutenberg, validate_semantic_html, validate_wxr

FIXTURES = Path(__file__).parent / "fixtures"


class ExportValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(
            (FIXTURES / "gutenberg" / "normalized.json").read_text(encoding="utf-8")
        )

    def test_semantic_html_summary(self):
        result = validate_semantic_html(self.document, render_html(self.document))
        self.assertTrue(result["valid"])
        self.assertEqual(result["headings"], 1)
        self.assertEqual(result["lists"], 2)
        self.assertEqual(result["tables"], 1)
        self.assertEqual(result["images"], 1)
        self.assertEqual(result["captions"], 2)
        self.assertEqual(result["serialization_errors"], [])
        self.assertEqual(result["h1_count"], 1)

    def test_semantic_html_requires_one_h1(self):
        result = validate_semantic_html(self.document, "<main><p>No title</p></main>")
        self.assertFalse(result["valid"])
        self.assertIn("Expected exactly one document H1; found 0", result["serialization_errors"])

    def test_gutenberg_fails_for_broken_internal_anchor(self):
        markup = '<!-- wp:paragraph -->\n<p><a href="#missing">Reference</a></p>\n<!-- /wp:paragraph -->'
        result = validate_gutenberg(self.document, markup)
        self.assertFalse(result["valid"])
        self.assertIn("Missing internal target: #missing", result["serialization_errors"])

    def test_gutenberg_summary_has_no_silent_drops(self):
        markup = render_gutenberg(self.document)
        result = validate_gutenberg(self.document, markup)
        self.assertTrue(result["valid"])
        self.assertEqual(result["skipped_block_count"], 0)
        self.assertEqual(result["fallback_unknown_count"], 0)
        self.assertIn("heading", result["block_names"])
        self.assertIn("table", result["block_names"])

    def test_wxr_summary_reads_multiple_items(self):
        markup = render_wxr(
            [
                {"key": "parent", "title": "Parent", "slug": "parent", "content": ""},
                {
                    "key": "child",
                    "parent": "parent",
                    "title": "Child",
                    "slug": "child",
                    "content": "",
                },
            ]
        )
        result = validate_wxr(markup)
        self.assertTrue(result["valid"])
        self.assertEqual(result["item_count"], 2)
        self.assertEqual(result["items"][1]["parent"], "1")


if __name__ == "__main__":
    unittest.main()
