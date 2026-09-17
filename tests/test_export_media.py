import json
import tempfile
import unittest
from pathlib import Path

from pdf_to_web.export import export_project
from pdf_to_web.project import create_project, save_project


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
            self.assertEqual({path.name for path in assets.iterdir()}, {"photo.png", "photo-2.png", "decor.png"})
            manifest = json.loads((project / "output" / "wordpress" / "reports" / "media-manifest.json").read_text())
            self.assertEqual(manifest["summary"], {"total": 6, "resolved": 2, "unresolved": 3, "decorative": 1, "copied_assets": 3})
            first = next(item for item in manifest["items"] if item["block_id"] == "local-1")
            self.assertEqual(first["source_page"], 2)
            self.assertEqual(first["alt_text"], "Login screen")
            self.assertEqual(first["caption"], "Select Log In")
            self.assertEqual(first["wordpress_status"], "unresolved")
            self.assertTrue((project / first["asset_path"]).is_file())
            self.assertTrue((project / "output" / "wordpress" / "reports" / "media-manifest.md").is_file())

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
