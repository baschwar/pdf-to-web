import json
import tempfile
import unittest
from pathlib import Path

from pdf_to_web.cli import main
from pdf_to_web.export_validation import compare_semantics, html_semantics, model_semantics, validate_export_corpus, validate_project_exports
from pdf_to_web.exporters.gutenberg import render_document as render_gutenberg
from pdf_to_web.project import create_project
from pdf_to_web.validation import validate_internal_links


FIXTURE = Path(__file__).parent / "fixtures" / "gutenberg" / "normalized.json"


class ExportGateTests(unittest.TestCase):
    def _project(self, root: Path, status: str = "review_ready", name: str = "project") -> Path:
        project = root / name
        create_project(project, "Validation")
        document = json.loads(FIXTURE.read_text(encoding="utf-8"))
        document["review"] = {"status": status, "issues": []}
        destination = project / "extraction" / "normalized" / "document.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(document), encoding="utf-8")
        return project

    def test_internal_anchor_validator_detects_missing_duplicate_and_empty_ids(self):
        result = validate_internal_links('<p id="same"><a href="#missing">x</a></p><p id="same"></p><i id=""></i>')
        self.assertFalse(result["valid"])
        self.assertEqual(result["duplicate_ids"], ["same"])
        self.assertEqual(result["empty_ids"], 1)
        self.assertEqual(result["missing_targets"], ["missing"])

    def test_semantic_snapshot_detects_content_loss_and_preserves_utf8(self):
        document = json.loads(FIXTURE.read_text(encoding="utf-8"))
        expected = model_semantics(document)
        actual = html_semantics("<h1>Access &amp; Equity – 2026</h1>")
        result = compare_semantics(expected, actual)
        self.assertFalse(result["valid"])
        self.assertTrue(any("link" in error for error in result["errors"]))

    def test_nested_table_in_list_item_is_not_lost_from_gutenberg(self):
        document = {
            "metadata": {"title": "Plan"},
            "blocks": [{"id": "l", "type": "list", "children": [{"id": "i", "type": "list_item", "content": "Year 3", "children": [{"id": "t", "type": "table", "rows": [["Fall", "Spring"], ["A", "B"]]}]}]}],
        }
        expected = model_semantics(document)
        actual = html_semantics(render_gutenberg(document))
        self.assertTrue(compare_semantics(expected, actual)["valid"])
        self.assertEqual(actual["tables"], [["Fall", "Spring", "A", "B"]])

    def test_nested_paragraph_does_not_merge_into_list_item(self):
        document = {
            "metadata": {"title": "Instructions"},
            "blocks": [{"id": "l", "type": "list", "children": [{"id": "i", "type": "list_item", "content": "Choose a course", "children": [{"id": "p", "type": "paragraph", "content": "Ask your advisor."}]}]}],
        }
        expected = model_semantics(document)
        actual = html_semantics(render_gutenberg(document))
        self.assertTrue(compare_semantics(expected, actual)["valid"])
        self.assertIn("Ask your advisor.", actual["paragraphs"])

    def test_project_gate_writes_json_and_markdown_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory))
            json_path, md_path = validate_project_exports(project)
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["result"], "PASS")
            self.assertTrue(md_path.is_file())
            self.assertTrue(report["formats"]["wxr"]["standalone_gutenberg_equivalent"]["valid"])
            self.assertEqual(report["formats"]["semantic_html"]["anchors"]["missing_targets"], [])

    def test_conversion_blocked_fails_closed_for_wordpress_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory), "conversion_blocked")
            json_path, _ = validate_project_exports(project)
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["result"], "PASS")
            self.assertTrue(report["formats"]["gutenberg"]["blocked_as_expected"])
            self.assertTrue(report["formats"]["wordpress-xml"]["blocked_as_expected"])

    def test_cli_returns_success_for_passing_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory))
            self.assertEqual(main(["validate-exports", "--project", str(project)]), 0)

    def test_corpus_gate_generates_result_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._project(root, name="one")
            self._project(root, name="two")
            json_path, md_path = validate_export_corpus(root)
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["result"], "PASS")
            self.assertEqual(len(report["documents"]), 2)
            self.assertIn("| Document project | Semantic |", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
