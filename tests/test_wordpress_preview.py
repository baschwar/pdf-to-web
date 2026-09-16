import json
import unittest
from pathlib import Path

from pdf_to_web.exporters import gutenberg
from pdf_to_web.wordpress_preview import preview_available, render_gutenberg_preview


@unittest.skipUnless(preview_available(), "Run npm install to enable WordPress preview tests")
class WordPressPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(
            Path("tests/fixtures/gutenberg/normalized.json").read_text(encoding="utf-8")
        )

    def test_core_export_round_trip(self):
        markup = gutenberg.render_document(self.document)
        preview = render_gutenberg_preview(markup)
        self.assertEqual(
            set(preview.block_types),
            {
                "core/paragraph",
                "core/heading",
                "core/list",
                "core/image",
                "core/quote",
                "core/table",
            },
        )
        self.assertEqual(preview.unsupported_blocks, ())
        for expected in ("<h1", "<p>", "<ul", "<img", "<blockquote", "<table"):
            self.assertIn(expected, preview.html)
        self.assertIn("Nested one", preview.html)
        self.assertNotIn("<table class=\"wp-block-table\">\n<figure", preview.html)

    def test_wsu_hero_section_and_nested_core_blocks(self):
        config = {
            "hero": {
                "enabled": True,
                "title": "Preview {Hero}",
                "headingTag": "h2",
                "caption": "Program caption",
                "imageSrc": "https://example.edu/hero.jpg",
                "backgroundType": "image",
                "className": "hero-class",
            },
            "section_defaults": {"id": "main", "className": "section-class"},
        }
        preview = render_gutenberg_preview(
            gutenberg.render_document(self.document, "wsuwp", config)
        )
        self.assertIn('<section class="wsu-preview-hero hero-class"', preview.html)
        self.assertIn('<img src="https://example.edu/hero.jpg"', preview.html)
        self.assertIn("<h2>Preview {Hero}</h2>", preview.html)
        self.assertIn("Program caption", preview.html)
        self.assertIn('<section id="main" class="wsu-preview-section section-class">', preview.html)
        self.assertIn("<p>Visit", preview.html)
        self.assertEqual(preview.unsupported_blocks, ())

    def test_unsupported_block_is_visible_and_recorded(self):
        preview = render_gutenberg_preview('<!-- wp:wsuwp/example {"value":"x"} /-->')
        self.assertEqual(preview.unsupported_blocks, ("wsuwp/example",))
        self.assertIn("WordPress block: wsuwp/example", preview.html)
        self.assertIn("Preview handler not implemented", preview.html)

    def test_generated_content_is_sanitized(self):
        markup = (
            '<!-- wp:html --><script>alert(1)</script>'
            '<img src="javascript:alert(1)" onerror="alert(1)">'
            '<p onclick="alert(1)">Safe text</p><!-- /wp:html -->'
        )
        preview = render_gutenberg_preview(markup)
        self.assertIn("Safe text", preview.html)
        self.assertNotIn("script", preview.html.lower())
        self.assertNotIn("javascript:", preview.html.lower())
        self.assertNotIn("onerror", preview.html.lower())
        self.assertNotIn("onclick", preview.html.lower())


if __name__ == "__main__":
    unittest.main()
