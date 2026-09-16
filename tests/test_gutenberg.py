import json
import unittest
from pathlib import Path

from pdf_to_web.exporters.gutenberg import render_document

FIXTURES = Path(__file__).parent / "fixtures"


class GutenbergTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(
            (FIXTURES / "gutenberg" / "normalized.json").read_text(encoding="utf-8")
        )

    def test_generic_blocks_and_escaping(self):
        output = render_document(self.document)
        self.assertIn('<!-- wp:heading {"level":1} -->', output)
        self.assertIn("<strong>details &amp; updates</strong>", output)
        self.assertIn('href="https://nursing.wsu.edu/?a=1&amp;b=2"', output)
        self.assertIn('<ul class="wp-block-list">', output)
        self.assertIn('<ol class="wp-block-list">', output)
        self.assertIn("<!-- wp:image -->", output)
        self.assertIn("<figcaption>Practice builds confidence.</figcaption>", output)
        self.assertIn("<!-- wp:quote -->", output)
        self.assertIn("<!-- wp:table -->", output)
        self.assertIn("Access &amp; Equity – 2026", output)

    def test_wsu_profile_with_image_id_and_sections(self):
        config = json.loads(
            (FIXTURES / "wsuwp" / "config-with-image-id.json").read_text(encoding="utf-8")
        )
        output = render_document(self.document, "wsuwp", config)
        self.assertIn('<!-- wp:wsuwp/hero {', output)
        self.assertIn('"imageId":54625', output)
        self.assertIn('"imageSrc":"https://wpcdn.web.wsu.edu/example.png"', output)
        self.assertIn("wsu\\u002dhero\\u002d\\u002dstyle\\u002dboxed", output)
        self.assertIn('<!-- wp:wsuwp/section {"id":"top"', output)
        self.assertIn("<!-- /wp:wsuwp/section -->", output)
        self.assertIn("<!-- wp:paragraph -->", output)

    def test_wsu_hero_does_not_invent_image_id(self):
        output = render_document(
            self.document,
            "wsuwp",
            {"hero": {"enabled": True, "imageSrc": "https://example.edu/hero.png"}},
        )
        self.assertIn('"imageSrc":"https://example.edu/hero.png"', output)
        self.assertNotIn('"imageId"', output)

    def test_production_fixture_contains_expected_wsu_nesting(self):
        sample = (FIXTURES / "wsuwp" / "production-sample.html").read_text(encoding="utf-8")
        self.assertLess(sample.index("<!-- wp:wsuwp/section"), sample.index("<!-- wp:heading -->"))
        self.assertLess(sample.index("<!-- wp:paragraph -->"), sample.index("<!-- /wp:wsuwp/section -->"))


if __name__ == "__main__":
    unittest.main()
