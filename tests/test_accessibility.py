import json
import tempfile
import unittest
from pathlib import Path

from pdf_to_web.accessibility import assess_document, save_decision, write_reports
from pdf_to_web.exporters import gutenberg, html


def fixture_document():
    return {
        "schema_version": "pdf-to-web-normalized-v1",
        "metadata": {"title": "Accessibility fixture"},
        "review": {
            "status": "review_ready",
            "issues": [{"code": "reading_order", "page": 2, "message": "Confirm reading order."}],
            "complex_visuals": [
                {"id": "chart-1", "type": "chart", "status": "needs_text_equivalent", "source_page": 2}
            ],
        },
        "blocks": [
            {"id": "h1", "type": "heading", "level": 1, "content": "Title", "review": {"status": "approved"}},
            {"id": "h3", "type": "heading", "level": 3, "content": "Skipped", "review": {"status": "approved"}},
            {"id": "image", "type": "image", "alt": "", "decorative": False, "review": {"status": "needs_review"}, "provenance": {"source_page": 1}},
            {"id": "table", "type": "table", "rows": [[{"content": "Name"}, {"content": "Value"}], [{"content": "A"}, {"content": "1"}]], "review": {"status": "approved"}, "provenance": {"source_page": 2}},
            {"id": "link", "type": "paragraph", "content": "Click here", "runs": [{"text": "Click here", "href": "https://example.edu"}], "review": {"status": "approved"}},
            {"id": "unknown", "type": "unknown", "content": "Unknown", "review": {"status": "needs_review"}},
        ],
    }


class AccessibilityTests(unittest.TestCase):
    def test_assessment_covers_phase3a_categories(self):
        report = assess_document(fixture_document())
        categories = {item["category"] for item in report["items"]}
        self.assertTrue({"images", "complex_visuals", "tables", "headings", "links", "unresolved_content", "diagnostics", "structure"}.issubset(categories))
        self.assertEqual(report["status"], "needs_review")
        self.assertGreater(report["summary"]["unresolved"], 0)

    def test_decisions_are_persisted_and_summarized(self):
        document = fixture_document()
        save_decision(document, "link:link:1", "approved", "Destination is clear in context.")
        item = next(item for item in assess_document(document)["items"] if item["id"] == "link:link:1")
        self.assertEqual(item["status"], "approved")
        self.assertEqual(item["note"], "Destination is clear in context.")

    def test_mechanical_failures_cannot_be_waived(self):
        with self.assertRaisesRegex(ValueError, "Resolve this finding in Structure"):
            save_decision(fixture_document(), "image-alt:image", "approved", "")

    def test_nested_list_items_do_not_duplicate_structure_findings(self):
        document = fixture_document()
        document["blocks"].append({
            "id": "list", "type": "list", "review": {"status": "needs_review"},
            "children": [{"id": "item", "type": "list_item", "content": "Nested", "review": {"status": "unreviewed"}}],
        })
        structural_ids = [item["id"] for item in assess_document(document)["items"] if item["category"] == "structure"]
        self.assertIn("structure:list", structural_ids)
        self.assertNotIn("structure:item", structural_ids)

    def test_reports_are_machine_and_human_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_reports(Path(directory), fixture_document())
            self.assertEqual({path.suffix for path in paths}, {".json", ".html"})
            report = json.loads(next(path for path in paths if path.suffix == ".json").read_text())
            self.assertEqual(report["schema_version"], "pdf-to-web-accessibility-v1")
            markup = next(path for path in paths if path.suffix == ".html").read_text()
            self.assertIn("This report records review decisions", markup)
            self.assertIn("Confirm reading order", markup)

    def test_reviewed_table_semantics_flow_to_both_exporters(self):
        block = {
            "id": "table",
            "type": "table",
            "caption": "Enrollment",
            "table_accessibility": {"reviewed": True, "header_row": True, "header_column": True},
            "rows": [[{"content": "Program"}, {"content": "Students"}], [{"content": "Nursing"}, {"content": "42"}]],
        }
        document = {"metadata": {"title": "Tables"}, "blocks": [block]}
        semantic = html.render_document(document)
        wordpress = gutenberg.render_document(document)
        for output in (semantic, wordpress):
            self.assertIn('scope="col"', output)
            self.assertIn('scope="row"', output)
            self.assertIn("Enrollment", output)


if __name__ == "__main__":
    unittest.main()
