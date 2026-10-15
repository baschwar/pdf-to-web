"""Compact image review retains authoring controls and read-only disclosures."""
import re
import unittest
import test_image_draft_routes as fixtures


class CompactImageReviewTests(unittest.TestCase):
    setUp = fixtures.ImageDraftRouteTests.setUp
    post = fixtures.ImageDraftRouteTests.post

    def test_compact_fields_and_optional_tools_preserve_saved_content(self):
        paths = [self.root / 'review/current.json', self.root / 'project.json']
        before = {p: p.read_bytes() for p in paths}
        page = self.client.get('/structure').text
        card = re.search(r'<article[^>]*id="block-photo".*?</article>', page, re.S)[0]
        self.assertLess(card.index('name="decorative"'), card.index('name="alt"'))
        self.assertIn('class="form-grid image-authoring-fields"', card)
        self.assertIn('name="alt" rows="2"', card)
        self.assertIn('name="caption" rows="2"', card)
        self.assertIn('class="image-long-description"', card)
        self.assertIn('name="long_description" rows="4"', card)
        self.assertLess(card.index('image-save-actions'), card.index('image-approval-scope'))
        self.assertIn('<details class="image-drafting-options">', card)
        self.assertIn('data-draft-action="export"', card)
        self.assertIn('Draft image descriptions', card)
        self.assertLess(card.index('image-save-actions'), card.index('Draft image descriptions'))
        self.assertIn('<details class="block-source-details">', card)
        self.assertLess(card.index('block-actions'), card.index('OpenDataLoader source:'))
        self.assertEqual({p: p.read_bytes() for p in paths}, before)

    def test_existing_request_stays_visible_in_optional_drafting_disclosure(self):
        self.assertEqual(self.post('export', {'block_ids': ['photo']}).status_code, 200)
        page = self.client.get('/structure').text
        card = re.search(r'<article[^>]*id="block-photo".*?</article>', page, re.S)[0]
        self.assertIn('<details class="image-drafting-options" open>', card)
        self.assertIn('Awaiting response', card)
        self.assertIn('data-draft-action="export-new"', card)


if __name__ == '__main__':
    unittest.main()
