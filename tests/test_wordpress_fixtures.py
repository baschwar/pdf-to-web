import json
import tempfile
import unittest
from pathlib import Path

from pdf_to_web.validation import validate_wxr
from pdf_to_web.wordpress_fixtures import fixture_sets, write_wordpress_fixtures


class WordPressFixtureTests(unittest.TestCase):
    def test_fixture_matrix_covers_round_trip_cases(self):
        fixtures = fixture_sets()
        self.assertEqual(
            set(fixtures),
            {
                "single-page.xml",
                "single-post.xml",
                "parent-child.xml",
                "multi-item.xml",
                "wsuwp-page.xml",
            },
        )
        self.assertIn("<!-- wp:wsuwp/hero", fixtures["wsuwp-page.xml"][0]["content"])
        self.assertIn("<!-- wp:wsuwp/section", fixtures["wsuwp-page.xml"][0]["content"])

    def test_generated_wxr_is_valid_and_defaults_to_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_wordpress_fixtures(Path(directory))
            self.assertEqual(len(paths), 6)
            expected = json.loads((Path(directory) / "expected.json").read_text())
            for filename, items in expected.items():
                with self.subTest(filename=filename):
                    summary = validate_wxr((Path(directory) / filename).read_text())
                    self.assertEqual(summary["serialization_errors"], [])
                    self.assertEqual(summary["item_count"], len(items))
                    self.assertEqual({item["status"] for item in summary["items"]}, {"draft"})


if __name__ == "__main__":
    unittest.main()
