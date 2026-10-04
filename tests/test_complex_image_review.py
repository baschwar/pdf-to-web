import copy
import re
import unittest
from urllib.parse import unquote

import test_image_draft_routes as routes
from pdf_to_web import image_drafts as drafts
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, undo_last
from pdf_to_web.web import _visual_image_url
from pdf_to_web.exporters.html import render_document


class ComplexImageReviewTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp
    post = routes.ImageDraftRouteTests.post

    def imported(self):
        entry = drafts.prepare(self.root, ['photo'])[0]
        drafts.import_response(self.root, self.fixture.response(entry), commit=True)
        doc = ensure_review_document(self.root)
        return doc, drafts.visual_for(doc, drafts.image(doc, 'photo'))

    def test_imported_image_and_short_alt_render_with_legacy_fallback(self):
        doc, visual = self.imported()
        self.assertEqual(visual['accessibility']['short_alt'], 'Accepted ALT')
        visual['accessibility'].pop('short_alt')
        save_review_document(self.root, doc)
        page = self.client.get('/structure').text
        card = page.split('id="block-photo"')[1].split('</article>')[0]
        self.assertIn('name="alt" rows="3">Accepted ALT</textarea>', card)
        url = re.search(r'<img[^>]+src="([^"]+)"', card).group(1)
        self.assertEqual(self.client.get(url).content, b'fixture image bytes')
        self.assertIn('id="visual-' + visual['id'] + '"', card)
        self.assertEqual(card.count('Text provided; awaiting manual review'), 1)

    def test_exact_asset_paths_are_supported_without_basename_guessing(self):
        doc = ensure_review_document(self.root)
        for ref, expected in [('images/photo.png', b'fixture image bytes'),
                              ('extraction/raw/images/photo.png', b'fixture image bytes'),
                              ('one.png', b'one.png'),
                              ('extraction/assets/images/two.png', b'two.png')]:
            url = _visual_image_url(self.root, doc, {'asset_references': [ref]})
            self.assertTrue(url.startswith('/api/image-drafts/asset?path='))
            self.assertEqual(self.client.get(url).content, expected)
        self.assertEqual(_visual_image_url(self.root, doc, {'asset_references': ['../outside.png']}), '')
        self.assertEqual(_visual_image_url(self.root, doc, {'asset_references': ['missing.png']}), '')

    def test_save_updates_image_alt_description_and_exports_with_undo(self):
        doc, visual = self.imported()
        before = copy.deepcopy(doc)
        response = self.client.post('/api/complex-visuals/' + visual['id'], headers=self.headers,
                                    json={'short_alt': 'Edited short alt', 'long_description': 'Edited equivalent', 'status': 'reclassified'})
        self.assertEqual(response.status_code, 200, response.text)
        current = ensure_review_document(self.root)
        self.assertEqual(drafts.image(current, 'photo')['alt'], 'Edited short alt')
        self.assertEqual(drafts.image(current, 'photo')['review']['status'], 'needs_review')
        self.assertIn('Edited short alt', render_document(current))
        self.assertIn('Edited equivalent', render_document(current))
        undo_last(self.root)
        restored = ensure_review_document(self.root)
        self.assertEqual(restored['blocks'], before['blocks'])
        self.assertEqual(restored['review']['complex_visuals'], before['review']['complex_visuals'])

    def test_image_editor_keeps_bound_short_alt_consistent(self):
        doc, visual = self.imported()
        update_block(self.root, 'photo', {'alt': 'New image alt'})
        current = ensure_review_document(self.root)
        self.assertEqual(drafts.visual_for(current, drafts.image(current, 'photo'))['accessibility']['short_alt'], 'New image alt')
        update_block(self.root, 'photo', {'decorative': True})
        current = ensure_review_document(self.root)
        self.assertEqual(drafts.visual_for(current, drafts.image(current, 'photo'))['accessibility']['short_alt'], '')

    def test_review_controls_precede_source_and_index_with_requested_order(self):
        page = self.client.get('/structure').text
        card = page.split('id="block-photo"')[1].split('</article>')[0]
        actions = card.split('class="block-review-actions"')[1].split('</div>')[0]
        self.assertLess(actions.index('Needs review'), actions.index('>Exclude<'))
        self.assertNotIn('>Approve<', actions)
        self.assertEqual(card.count('data-save-and-approve'), 1)
        self.assertLess(card.index('block-review-actions'), card.index('<header>'))
        self.assertLess(card.index('block-review-actions'), card.index('source-provenance'))
        footer = card.split('<footer')[1]
        self.assertNotIn('data-action="approve"', footer)
        self.assertNotIn('data-action="flag"', footer)
