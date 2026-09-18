import json
import tempfile
import unittest
from pathlib import Path

from pdf_to_web.exporters import gutenberg, html
from pdf_to_web.project import create_project
from pdf_to_web.review_state import (
    ensure_review_document,
    archive_review_document,
    merge_with_next,
    move_block,
    original_path,
    review_progress,
    split_block,
    undo_last,
    update_block,
    update_complex_visual,
)


def fixture_document(status="review_ready"):
    return {
        "schema_version": "pdf-to-web-normalized-v1",
        "metadata": {"title": "Review fixture", "page_count": 1},
        "review": {"status": status, "issues": [], "complex_visuals": []},
        "blocks": [
            {"id": "h1", "type": "heading", "level": 1, "content": "Review fixture", "provenance": {"source_page": 1}},
            {"id": "p1", "type": "paragraph", "content": "First paragraph.", "provenance": {"source_page": 1}},
            {"id": "p2", "type": "paragraph", "content": "Second paragraph.", "provenance": {"source_page": 1}},
            {"id": "u1", "type": "unknown", "content": "Uncertain", "provenance": {"source_page": 1, "raw": {"type": "aside"}}},
        ],
    }


class ReviewStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        create_project(self.project, "Review fixture")
        path = original_path(self.project)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fixture_document()), encoding="utf-8")

    def read_original(self):
        return json.loads(original_path(self.project).read_text())

    def test_review_initialization_preserves_normalized_original(self):
        before = self.read_original()
        current = ensure_review_document(self.project)
        self.assertEqual(self.read_original(), before)
        self.assertEqual(current["blocks"][0]["review"]["status"], "unreviewed")
        self.assertEqual(current["blocks"][3]["review"]["status"], "needs_review")

    def test_type_level_text_and_review_state_persist(self):
        update_block(self.project, "u1", {"type": "heading", "level": 3, "content": "Corrected", "review_status": "approved"})
        reopened = ensure_review_document(self.project)
        block = reopened["blocks"][3]
        self.assertEqual((block["type"], block["level"], block["content"]), ("heading", 3, "Corrected"))
        self.assertEqual(block["review"]["status"], "approved")
        self.assertEqual(self.read_original()["blocks"][3]["type"], "unknown")

    def test_excluded_block_is_omitted_from_all_current_exports(self):
        update_block(self.project, "p1", {"review_status": "excluded"})
        current = ensure_review_document(self.project)
        self.assertNotIn("First paragraph", html.render_document(current))
        self.assertNotIn("First paragraph", gutenberg.render_document(current))
        self.assertIn("First paragraph", json.dumps(self.read_original()))

    def test_reorder_merge_split_and_undo(self):
        move_block(self.project, "p2", "up")
        self.assertEqual([block["id"] for block in ensure_review_document(self.project)["blocks"]][:3], ["h1", "p2", "p1"])
        merge_with_next(self.project, "p2")
        merged = ensure_review_document(self.project)
        self.assertIn("First paragraph", merged["blocks"][1]["content"])
        split_block(self.project, "p2", len("Second paragraph."))
        split = ensure_review_document(self.project)
        self.assertEqual(split["blocks"][2]["id"], "p2-split-1")
        undo_last(self.project)
        self.assertEqual(len(ensure_review_document(self.project)["blocks"]), 3)

    def test_move_to_start_and_end(self):
        move_block(self.project, "p1", "end")
        self.assertEqual(ensure_review_document(self.project)["blocks"][-1]["id"], "p1")
        move_block(self.project, "p1", "start")
        self.assertEqual(ensure_review_document(self.project)["blocks"][0]["id"], "p1")
        self.assertTrue(ensure_review_document(self.project)["review_session"]["manual_order_override"])

    def test_revised_legacy_review_order_is_not_automatically_reconciled(self):
        current = ensure_review_document(self.project)
        current["review_session"]["revision"] = 1
        current["blocks"][1]["provenance"]["bounding_box"] = [20, 200, 80, 220]
        current["blocks"][2]["type"] = "table"
        current["blocks"][2]["rows"] = [[{"content": "Data"}]]
        current["blocks"][2]["provenance"]["bounding_box"] = [20, 100, 500, 199]
        (self.project / "review" / "current.json").write_text(json.dumps(current), encoding="utf-8")
        reopened = ensure_review_document(self.project)
        self.assertNotIn("reading_order", reopened)
        self.assertEqual([block["id"] for block in reopened["blocks"][:3]], ["h1", "p1", "p2"])

    def test_list_text_edit_builds_exportable_items(self):
        update_block(self.project, "u1", {"type": "list", "content": "One\nTwo", "review_status": "needs_review"})
        block = ensure_review_document(self.project)["blocks"][3]
        self.assertEqual([item["content"] for item in block["children"]], ["One", "Two"])
        self.assertIn("<li>One</li>", html.render_document(ensure_review_document(self.project)))

    def test_review_progress(self):
        update_block(self.project, "p1", {"review_status": "approved"})
        update_block(self.project, "p2", {"review_status": "excluded"})
        progress = review_progress(ensure_review_document(self.project))
        self.assertEqual(progress["total"], 4)
        self.assertEqual(progress["approved"], 1)
        self.assertEqual(progress["excluded"], 1)
        self.assertEqual(progress["needs_review"], 1)

    def test_image_accessibility_fields_and_approval(self):
        document = self.read_original()
        document["blocks"].append({"id": "image-1", "type": "image", "src": "images/screen.png", "alt": "", "decorative": False, "provenance": {"source_page": 1}})
        original_path(self.project).write_text(json.dumps(document))

        with self.assertRaisesRegex(ValueError, "Add alt text"):
            update_block(self.project, "image-1", {"review_status": "approved"})
        update_block(self.project, "image-1", {"alt": "Student completing the registration form", "caption": "Registration step", "decorative": False, "review_status": "approved"})
        image = ensure_review_document(self.project)["blocks"][-1]
        self.assertEqual(image["alt"], "Student completing the registration form")
        self.assertEqual(image["caption"], "Registration step")
        self.assertEqual(image["review"]["status"], "approved")
        self.assertIn('alt="Student completing the registration form"', html.render_document(ensure_review_document(self.project)))

        update_block(self.project, "image-1", {"decorative": True, "review_status": "approved"})
        image = ensure_review_document(self.project)["blocks"][-1]
        self.assertTrue(image["decorative"])
        self.assertEqual(image["alt"], "")

    def test_approved_image_without_alt_returns_to_needs_review(self):
        current = ensure_review_document(self.project)
        current["blocks"].append({"id": "legacy-image", "type": "image", "src": "images/legacy.png", "alt": "", "decorative": False, "provenance": {"source_page": 1}, "review": {"status": "approved", "updated_at": "earlier"}})
        (self.project / "review" / "current.json").write_text(json.dumps(current))
        reopened = ensure_review_document(self.project)
        self.assertEqual(reopened["blocks"][-1]["review"]["status"], "needs_review")

    def test_archive_preserves_review_before_normalized_regeneration(self):
        update_block(self.project, "p1", {"content": "Reviewed"})
        archived = archive_review_document(self.project, "regenerated")
        self.assertIsNotNone(archived)
        self.assertIn("Reviewed", archived.read_text())
        self.assertFalse((self.project / "review" / "current.json").exists())

    def test_complex_visual_review_persists(self):
        document = self.read_original()
        document["review"]["complex_visuals"] = [{"id": "visual-1", "type": "infographic", "status": "needs_text_equivalent", "recovered_text": "Old"}]
        original_path(self.project).write_text(json.dumps(document))
        update_complex_visual(self.project, "visual-1", {"type": "chart", "status": "reclassified", "recovered_text": "Corrected"})
        visual = ensure_review_document(self.project)["review"]["complex_visuals"][0]
        self.assertEqual((visual["type"], visual["status"], visual["recovered_text"]), ("chart", "reclassified", "Corrected"))


if __name__ == "__main__":
    unittest.main()
