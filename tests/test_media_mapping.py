import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from pdf_to_web.media_mapping import (
    MAPPING_FIELDS,
    apply_media_mapping,
    apply_wordpress_media_export,
)
from pdf_to_web.project import create_project
from pdf_to_web.review_state import ensure_review_document, original_path


class MediaMappingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        create_project(self.project, "Media")
        path = original_path(self.project)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema_version": "pdf-to-web-normalized-v1",
            "metadata": {"title": "Media"},
            "blocks": [
                {"id": "image-1", "type": "image", "src": "images/one.png", "alt": "Old", "caption": ""},
                {"id": "decor", "type": "image", "src": "images/decor.png", "decorative": True},
            ],
        }), encoding="utf-8")

    def mapping(self, **values):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=MAPPING_FIELDS)
        writer.writeheader()
        writer.writerow({"block_id": "image-1", "asset_filename": "one.png", **values})
        return stream.getvalue()

    def test_import_persists_url_attachment_alt_and_caption(self):
        result = apply_media_mapping(self.project, self.mapping(
            wordpress_attachment_id="42",
            wordpress_url="https://example.edu/uploads/one.png",
            alt_text="Updated alt",
            caption="Updated caption",
        ))
        self.assertEqual(result, {"mapped": 1, "skipped": 0, "remaining": 0})
        block = ensure_review_document(self.project)["blocks"][0]
        self.assertEqual(block["wordpress_attachment_id"], 42)
        self.assertEqual(block["wordpress_url"], "https://example.edu/uploads/one.png")
        self.assertEqual(block["alt"], "Updated alt")
        self.assertEqual(block["caption"], "Updated caption")

    def test_import_rejects_unknown_blocks_and_invalid_urls(self):
        with self.assertRaisesRegex(ValueError, "HTTP"):
            apply_media_mapping(self.project, self.mapping(wordpress_url="/uploads/one.png"))
        bad = self.mapping(wordpress_url="https://example.edu/one.png").replace("image-1", "missing")
        with self.assertRaisesRegex(ValueError, "Unknown"):
            apply_media_mapping(self.project, bad)

    def test_wordpress_media_export_updates_csv_and_review_document(self):
        mapping_path = self.project / "output" / "wordpress" / "reports" / "media-mapping.csv"
        mapping_path.parent.mkdir(parents=True)
        mapping_path.write_text(self.mapping(alt_text="Updated alt", caption="Caption"))
        xml = '''<?xml version="1.0"?>
<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel><item>
<wp:post_id>73</wp:post_id><wp:post_type>attachment</wp:post_type>
<wp:attachment_url>https://example.edu/wp-content/uploads/2026/09/one.png</wp:attachment_url>
<wp:postmeta><wp:meta_key>_wp_attached_file</wp:meta_key><wp:meta_value>2026/09/one.png</wp:meta_value></wp:postmeta>
</item></channel></rss>'''
        result = apply_wordpress_media_export(self.project, xml)
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["remaining"], 0)
        with mapping_path.open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["wordpress_attachment_id"], "73")
        self.assertEqual(row["wordpress_url"], "https://example.edu/wp-content/uploads/2026/09/one.png")
        block = ensure_review_document(self.project)["blocks"][0]
        self.assertEqual(block["wordpress_attachment_id"], 73)

    def test_wordpress_media_export_reports_unmatched_and_ambiguous(self):
        mapping_path = self.project / "output" / "wordpress" / "reports" / "media-mapping.csv"
        mapping_path.parent.mkdir(parents=True)
        mapping_path.write_text(self.mapping())
        xml = '''<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel>
<item><wp:post_id>1</wp:post_id><wp:post_type>attachment</wp:post_type><wp:attachment_url>https://example.edu/one.png</wp:attachment_url></item>
<item><wp:post_id>2</wp:post_id><wp:post_type>attachment</wp:post_type><wp:attachment_url>https://cdn.example.edu/one.png</wp:attachment_url></item>
</channel></rss>'''
        result = apply_wordpress_media_export(self.project, xml)
        self.assertEqual(result["matched"], 0)
        self.assertEqual(result["ambiguous"], 1)
        with self.assertRaisesRegex(ValueError, "document type"):
            apply_wordpress_media_export(self.project, "<!DOCTYPE rss><rss />")
