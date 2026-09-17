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

    def test_ordered_list_types_match_wordpress_serialized_html(self):
        document = {
            "blocks": [
                {"type": "list", "ordered": True, "marker_style": "decimal", "children": [{"type": "list_item", "content": "One"}]},
                {"type": "list", "ordered": True, "marker_style": "lower-alpha", "children": [{"type": "list_item", "content": "Alpha"}]},
                {"type": "list", "ordered": True, "marker_style": "upper-roman", "children": [{"type": "list_item", "content": "Roman"}]},
            ]
        }
        output = render_document(document)
        self.assertIn('<!-- wp:list {"ordered":true} -->\n<ol class="wp-block-list">', output)
        self.assertIn('<!-- wp:list {"ordered":true,"type":"a"} -->\n<ol type="a" class="wp-block-list">', output)
        self.assertIn('<!-- wp:list {"ordered":true,"type":"I"} -->\n<ol type="I" class="wp-block-list">', output)
        self.assertNotIn('"type":"decimal"', output)
        self.assertNotIn('"type":"lower-alpha"', output)

    def test_empty_paragraphs_are_not_exported_as_editor_spacers(self):
        output = render_document({"blocks": [{"type": "paragraph", "content": "  "}]})
        self.assertEqual(output, "\n")

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

    def test_wsu_section_is_opt_in(self):
        output = render_document(self.document, "wsuwp", {})
        self.assertNotIn("wp:wsuwp/section", output)

    def test_production_fixture_contains_expected_wsu_nesting(self):
        sample = (FIXTURES / "wsuwp" / "production-sample.html").read_text(encoding="utf-8")
        self.assertLess(sample.index("<!-- wp:wsuwp/section"), sample.index("<!-- wp:heading -->"))
        self.assertLess(sample.index("<!-- wp:paragraph -->"), sample.index("<!-- /wp:wsuwp/section -->"))

    def test_production_style_hero_and_section_fixtures(self):
        document = {
            "metadata": {"title": "Student Academic Onboarding"},
            "blocks": [
                {"id": "h", "type": "heading", "level": 2, "content": "Welcome"},
                {"id": "p", "type": "paragraph", "content": "Let's get started"},
            ],
        }
        scenarios = [
            ("hero-title.html", {"enabled": True}),
            ("hero-caption.html", {"enabled": True, "caption": "RN-BSN"}),
            (
                "hero-image-src.html",
                {"enabled": True, "imageSrc": "https://wpcdn.web.wsu.edu/hero-image.png"},
            ),
            (
                "hero-image-id.html",
                {
                    "enabled": True,
                    "imageId": 54625,
                    "imageSrc": "https://wpcdn.web.wsu.edu/hero-image.png",
                },
            ),
        ]
        for fixture, hero in scenarios:
            with self.subTest(fixture=fixture):
                output = render_document(document, "wsuwp", {"hero": hero})
                expected = (FIXTURES / "wsuwp" / fixture).read_text(encoding="utf-8").strip()
                self.assertEqual(output.split("\n", 1)[0], expected)
        output = render_document(
            document,
            "wsuwp",
            {
                "section_defaults": {
                    "id": "top",
                    "className": "wsu-color-background--white",
                }
            },
        )
        section = (FIXTURES / "wsuwp" / "section.html").read_text(encoding="utf-8").strip()
        self.assertEqual(output.split("\n", 1)[0], section)
        self.assertIn("<!-- wp:heading -->", output)
        self.assertIn("<!-- wp:paragraph -->", output)

    def test_footnotes_render_as_end_document_blocks(self):
        document = {
            "metadata": {"title": "Footnote sample"},
            "blocks": [
                {
                    "id": "p",
                    "type": "paragraph",
                    "content": "Claim 1.",
                    "footnote_references": [
                        {
                            "id": "fnref-1",
                            "footnote_id": "fn-1",
                            "marker": "1",
                            "start": 6,
                            "end": 7,
                        }
                    ],
                },
                {
                    "id": "fn-body",
                    "type": "paragraph",
                    "content": "1. Footnote text.",
                    "export_as_footnote_body": True,
                },
            ],
            "footnotes": [
                {
                    "id": "fn-1",
                    "marker": "1",
                    "text": "Footnote text.",
                    "references": [{"id": "fnref-1", "marker": "1"}],
                }
            ],
        }
        output = render_document(document)
        self.assertIn('<a href="#fn-1" id="fnref-1">1</a>', output)
        self.assertIn('<!-- wp:html -->', output)
        self.assertIn('<h2 id="footnotes-heading">Footnotes</h2>', output)
        self.assertIn('<li id="fn-1">Footnote text.', output)
        self.assertIn('aria-label="Back to footnote reference 1"', output)
        self.assertNotIn("1. Footnote text.</p>", output)


if __name__ == "__main__":
    unittest.main()
