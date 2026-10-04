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

    def test_import_persists_attachment_and_preserves_authored_alt_and_caption(self):
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
        self.assertEqual(block["alt"], "Old")
        self.assertEqual(block["caption"], "")

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
        self.assertEqual(result['ambiguous_images'][0]['block_id'], 'image-1')
        self.assertEqual(result['ambiguous_images'][0]['asset_filename'], 'one.png')
        with self.assertRaisesRegex(ValueError, "document type"):
            apply_wordpress_media_export(self.project, "<!DOCTYPE rss><rss />")

    def test_existing_mapping_is_not_replaced_by_ambiguous_missing_or_different_url(self):
        mapping_path = self.project / 'output/wordpress/reports/media-mapping.csv'
        mapping_path.parent.mkdir(parents=True)
        mapping_path.write_text(self.mapping())
        apply_media_mapping(self.project, self.mapping(wordpress_url='https://example.edu/one.png', wordpress_attachment_id='42'))
        initial = ensure_review_document(self.project)
        saved = (self.project / 'review/current.json').read_bytes()
        def item(identity, url, post_type='attachment'):
            return f'<item><wp:post_type>{post_type}</wp:post_type><wp:post_id>{identity}</wp:post_id><wp:attachment_url>{url}</wp:attachment_url></item>'
        for name, items, result_field in [
            ('missing', '', 'unmatched'),
            ('renamed', item(80, 'https://example.edu/one-1.png'), 'unmatched'),
            ('page-export', item(80, 'https://example.edu/one.png', 'page'), 'unmatched'),
            ('duplicate', item(42, 'https://example.edu/one.png') + item(80, 'https://example.edu/one.png'), 'ambiguous'),
            ('another-site', item(80, 'https://different.example.edu/one.png'), 'existing_kept'),
        ]:
            with self.subTest(name=name):
                xml = f'<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel>{items}</channel></rss>'
                result = apply_wordpress_media_export(self.project, xml, refresh_existing=True)
                self.assertEqual((result['matched'], result['mapped'], result['existing_kept']), (0, 0, 1))
                self.assertEqual(result[result_field], 1)
                self.assertEqual(ensure_review_document(self.project)['blocks'], initial['blocks'])
                self.assertEqual((self.project / 'review/current.json').read_bytes(), saved)
                details = result['unmatched_images'] + result['ambiguous_images'] + result['retained_images']
                self.assertEqual([r['block_id'] for r in details], ['image-1'])
                self.assertIn('kept', details[0]['reason'])

    def test_reuploaded_media_id_never_approves_pending_content(self):
        from pdf_to_web.review_state import update_block
        mapping_path = self.project / 'output/wordpress/reports/media-mapping.csv'
        mapping_path.parent.mkdir(parents=True)
        mapping_path.write_text(self.mapping())
        apply_media_mapping(self.project, self.mapping(wordpress_url='https://example.edu/one.png', wordpress_attachment_id='42'))
        update_block(self.project, 'image-1', {'review_status': 'needs_review'})
        before = ensure_review_document(self.project)
        xml = '<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel><item><wp:post_type>attachment</wp:post_type><wp:post_id>80</wp:post_id><wp:attachment_url>https://example.edu/one.png</wp:attachment_url></item></channel></rss>'
        result = apply_wordpress_media_export(self.project, xml, refresh_existing=True)
        after = ensure_review_document(self.project)
        self.assertEqual((result['matched'], result['mapped']), (1, 1))
        self.assertEqual(after['blocks'][0]['wordpress_attachment_id'], 80)
        self.assertEqual(after['blocks'][0]['review'], before['blocks'][0]['review'])
        self.assertEqual(after['blocks'][0]['review']['status'], 'needs_review')

    def test_xml_matching_preserves_newer_review_text_and_undo(self):
        from pdf_to_web.review_state import update_block, undo_last
        mapping_path = self.project / 'output/wordpress/reports/media-mapping.csv'
        mapping_path.parent.mkdir(parents=True)
        mapping_path.write_text(self.mapping(alt_text='Stale alternative', caption='Stale caption'))
        update_block(self.project, 'image-1', {'alt': 'Reviewed alternative', 'caption': 'Reviewed caption'})
        xml = '''<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel><item>
<wp:post_id>73</wp:post_id><wp:post_type>attachment</wp:post_type>
<wp:attachment_url>https://example.edu/one.png</wp:attachment_url>
</item></channel></rss>'''
        result = apply_wordpress_media_export(self.project, xml)
        self.assertEqual(result['matched'], 1)
        block = ensure_review_document(self.project)['blocks'][0]
        self.assertEqual(block['alt'], 'Reviewed alternative')
        self.assertEqual(block['caption'], 'Reviewed caption')
        undo_last(self.project)
        block = ensure_review_document(self.project)['blocks'][0]
        self.assertNotIn('wordpress_url', block)
        self.assertEqual(block['alt'], 'Reviewed alternative')

    def test_xml_matching_skips_content_excluded_after_preparation(self):
        from pdf_to_web.review_state import update_block
        mapping_path = self.project / 'output/wordpress/reports/media-mapping.csv'
        mapping_path.parent.mkdir(parents=True)
        mapping_path.write_text(self.mapping())
        update_block(self.project, 'image-1', {'review_status': 'excluded'})
        result = apply_wordpress_media_export(self.project, '''<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel><item>
<wp:post_id>73</wp:post_id><wp:post_type>attachment</wp:post_type>
<wp:attachment_url>https://example.edu/one.png</wp:attachment_url>
</item></channel></rss>''')
        self.assertEqual(result['matched'], 0)
        self.assertEqual(result['remaining'], 0)
        self.assertNotIn('wordpress_url', ensure_review_document(self.project)['blocks'][0])
