import unittest
import xml.etree.ElementTree as ET

from pdf_to_web.exporters.wxr import CONTENT_NS, EXCERPT_NS, WP_NS, render_wxr


class WxrTests(unittest.TestCase):
    def test_page_hierarchy_and_gutenberg_content(self):
        xml = render_wxr(
            [
                {
                    "key": "parent",
                    "title": "Impact & Report",
                    "slug": "impact-report",
                    "post_type": "page",
                    "status": "draft",
                    "excerpt": 'A "short" excerpt',
                    "content": "<!-- wp:paragraph -->\n<p>Café &amp; care</p>\n<!-- /wp:paragraph -->",
                },
                {
                    "key": "child",
                    "parent": "parent",
                    "title": "Research",
                    "slug": "research",
                    "post_type": "page",
                    "content": "<!-- wp:heading -->\n<h2>Research</h2>\n<!-- /wp:heading -->",
                },
            ]
        )
        root = ET.fromstring(xml)
        items = root.findall("./channel/item")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].findtext(f"{{{WP_NS}}}status"), "draft")
        self.assertEqual(items[1].findtext(f"{{{WP_NS}}}post_parent"), "1")
        self.assertIn("<!-- wp:paragraph -->", items[0].findtext(f"{{{CONTENT_NS}}}encoded"))
        self.assertEqual(items[0].findtext(f"{{{EXCERPT_NS}}}encoded"), 'A "short" excerpt')

    def test_post_taxonomies(self):
        xml = render_wxr(
            [
                {
                    "key": "story",
                    "title": "Story",
                    "slug": "story",
                    "post_type": "post",
                    "categories": ["Research"],
                    "tags": ["Rural Health"],
                    "content": "",
                }
            ]
        )
        root = ET.fromstring(xml)
        item = root.find("./channel/item")
        self.assertEqual(item.findtext(f"{{{WP_NS}}}post_type"), "post")
        terms = {(node.get("domain"), node.text) for node in item.findall("category")}
        self.assertEqual(terms, {("category", "Research"), ("post_tag", "Rural Health")})

    def test_custom_post_type_is_not_hard_coded(self):
        xml = render_wxr(
            [
                {
                    "key": "source-document",
                    "title": "Source document",
                    "slug": "source-document",
                    "post_type": "document",
                    "status": "draft",
                    "content": "<!-- wp:paragraph -->\n<p>Accessible version</p>\n<!-- /wp:paragraph -->",
                }
            ]
        )
        root = ET.fromstring(xml)
        item = root.find("./channel/item")
        self.assertEqual(item.findtext(f"{{{WP_NS}}}post_type"), "document")


if __name__ == "__main__":
    unittest.main()
