import csv
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from pdf_to_web.export import export_project, _write_media_manifest
from pdf_to_web.project import create_project, save_project
from pdf_to_web.review_state import ensure_review_document, save_review_document, move_block, update_block


class WordPressMediaExportTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "project"
        state = create_project(project, "Media fixture")
        state["source"].update({"original_filename": "Media Fixture.pdf"})
        save_project(project, state)
        raw = project / "extraction" / "raw"
        (raw / "images").mkdir(parents=True, exist_ok=True)
        (raw / "other").mkdir(parents=True, exist_ok=True)
        (raw / "images" / "photo.png").write_bytes(b"first")
        (raw / "other" / "photo.png").write_bytes(b"second")
        (raw / "images" / "decor.png").write_bytes(b"decorative")
        document = {
            "schema_version": "pdf-to-web-normalized-v1",
            "metadata": {"title": "Media fixture"},
            "review": {"status": "review_ready", "issues": []},
            "blocks": [
                {"id": "h", "type": "heading", "level": 1, "content": "Media fixture"},
                {"id": "local-1", "type": "image", "src": "images/photo.png", "alt": "Login screen", "caption": "Select Log In", "decorative": False, "provenance": {"source_page": 2}},
                {"id": "local-2", "type": "image", "src": "other/photo.png", "alt": "Second screen", "caption": "Continue", "decorative": False, "provenance": {"source_page": 3}},
                {"id": "decor", "type": "image", "src": "images/decor.png", "alt": "Ignored alt", "caption": "", "decorative": True, "provenance": {"source_page": 1}},
                {"id": "resolved-id", "type": "image", "src": "images/not-used.png", "wordpress_url": "https://cdn.example.edu/resolved.png", "wordpress_attachment_id": 12345, "alt": "Resolved", "caption": "Published image", "decorative": False, "provenance": {"source_page": 4}},
                {"id": "resolved-url", "type": "image", "src": "https://cdn.example.edu/url-only.png", "alt": "URL only", "caption": "", "decorative": False, "provenance": {"source_page": 5}},
                {"id": "invalid-config", "type": "image", "src": "images/missing.png", "wordpress_url": "/local/not-publishable.png", "alt": "Invalid mapping", "caption": "", "decorative": False, "provenance": {"source_page": 6}},
            ],
        }
        for block in document['blocks']:
            block['review'] = {'status': 'approved'}
        normalized = project / "extraction" / "normalized" / "document.json"
        normalized.parent.mkdir(parents=True, exist_ok=True)
        normalized.write_text(json.dumps(document), encoding="utf-8")
        return project

    def test_wordpress_media_package_preserves_metadata_without_broken_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory))
            paths = export_project(project, "gutenberg")
            markup = paths[0].read_text(encoding="utf-8")
            self.assertNotIn('src="images/photo.png"', markup)
            self.assertNotIn('src="other/photo.png"', markup)
            self.assertEqual(markup.count('data-pdf-to-web-media="unresolved"'), 3)
            self.assertIn('data-alt="Login screen"', markup)
            self.assertIn('data-caption="Select Log In"', markup)
            self.assertIn('src="https://cdn.example.edu/resolved.png"', markup)
            self.assertIn('class="wp-image-12345"', markup)
            self.assertIn('src="https://cdn.example.edu/url-only.png"', markup)
            self.assertNotIn('wp-image-None', markup)
            self.assertNotIn('/local/not-publishable.png', markup)
            self.assertIn("decorative unresolved image omitted", markup)

            assets = project / "output" / "wordpress" / "assets"
            self.assertEqual({path.name for path in assets.iterdir()}, {"media-fixture-image1.png", "media-fixture-image2.png", "media-fixture-image3.png"})
            manifest = json.loads((project / "output" / "wordpress" / "reports" / "media-manifest.json").read_text())
            self.assertEqual(manifest["summary"], {"total": 6, "resolved": 2, "unresolved": 3, "decorative": 1, "copied_assets": 3})
            first = next(item for item in manifest["items"] if item["block_id"] == "local-1")
            self.assertEqual(first["source_page"], 2)
            self.assertEqual(first["alt_text"], "Login screen")
            self.assertEqual(first["caption"], "Select Log In")
            self.assertEqual(first["wordpress_status"], "unresolved")
            self.assertTrue((project / first["asset_path"]).is_file())
            self.assertTrue((project / "output" / "wordpress" / "reports" / "media-manifest.md").is_file())
            mapping = project / "output" / "wordpress" / "reports" / "media-mapping.csv"
            with mapping.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual({row["block_id"] for row in rows}, {"local-1", "local-2", "resolved-id", "resolved-url", "invalid-config"})
            package = project / "output" / "wordpress" / "media-upload.zip"
            with zipfile.ZipFile(package) as archive:
                self.assertEqual(set(archive.namelist()), {"media-fixture-image1.png", "media-fixture-image2.png", "media-fixture-image3.png"})
                self.assertEqual(archive.read('media-fixture-image1.png'), b'first')
            self.assertEqual((project / 'extraction/raw/images/photo.png').read_bytes(), b'first')

    def test_custom_names_stable_after_reorder_exclusion_and_prefix_change(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory))
            document = ensure_review_document(project)
            document['media_export'] = {'image_prefix': 'citi-training-'}
            save_review_document(project, document)
            _, first = _write_media_manifest(project, document)
            before = {item['block_id']: item['asset_filename'] for item in first['items']}
            move_block(project, 'local-2', 'start')
            update_block(project, 'local-1', {'review_status': 'excluded'})
            document = ensure_review_document(project)
            _, later = _write_media_manifest(project, document)
            second = next(item for item in later['items'] if item['block_id'] == 'local-2')
            self.assertEqual(second['asset_filename'], before['local-2'])
            self.assertEqual(second['asset_filename'], 'citi-training-image2.png')
            document['media_export']['image_prefix'] = 'new-prefix-'
            _write_media_manifest(project, document)
            with zipfile.ZipFile(project / 'output/wordpress/media-upload.zip') as archive:
                self.assertEqual(set(archive.namelist()), {'new-prefix-image2.png', 'new-prefix-image3.png'})

    def test_semantic_html_copies_named_assets_and_uses_mapped_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory))
            outputs = export_project(project, 'html')
            markup = outputs[0].read_text()
            self.assertIn('src="assets/media-fixture-image1.png"', markup)
            self.assertIn('src="https://cdn.example.edu/resolved.png"', markup)
            self.assertTrue((outputs[0].parent / 'assets/media-fixture-image1.png').is_file())

    def test_excluded_parent_does_not_package_nested_images(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory))
            document = ensure_review_document(project)
            document['blocks'] = [{'id': 'parent', 'type': 'list', 'excluded': True, 'children': document['blocks']}]
            _, manifest = _write_media_manifest(project, document)
            self.assertEqual(manifest['summary']['total'], 0)
            with zipfile.ZipFile(project / 'output/wordpress/media-upload.zip') as archive:
                self.assertEqual(archive.namelist(), [])

    def test_wxr_never_serializes_local_image_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(Path(directory))
            wxr_path = export_project(project, "wordpress-xml")[0]
            markup = wxr_path.read_text(encoding="utf-8")
            self.assertNotIn('src="images/photo.png"', markup)
            self.assertNotIn('src="other/photo.png"', markup)
            self.assertIn('data-pdf-to-web-media="unresolved"', markup)
            self.assertIn("https://cdn.example.edu/resolved.png", markup)


if __name__ == "__main__":
    unittest.main()
