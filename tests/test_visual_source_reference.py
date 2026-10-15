"""Page-level review findings show their actual scope without inventing an image owner."""
import copy
import json
import unittest
from pathlib import Path

import test_web_app as fixtures
from pdf_to_web.project import load_project, save_project
from pdf_to_web.review_state import ensure_review_document, save_review_document, review_path
from pdf_to_web.web import _visual_reference, _source_page_visual_reviews
from review_helpers import stamp_fixture_approvals
from pdf_to_web.image_review import review_token


class VisualSourceReferenceTests(unittest.TestCase):
    setUp = fixtures.WebAppTests.setUp
    bootstrap = fixtures.WebAppTests.bootstrap
    headers = fixtures.WebAppTests.headers

    def standalone(self):
        self.bootstrap()
        project = load_project(self.project)
        project['source']['page_count'] = 14
        save_project(self.project, project)
        doc = ensure_review_document(self.project)
        stamp_fixture_approvals(doc)
        doc['review']['complex_visuals'] = [
            {'id': 'page-check-13', 'source_page': 13, 'type': 'infographic',
             'status': 'needs_text_equivalent', 'asset_references': [],
             'recovered_text': 'Retained source words'}]
        return save_review_document(self.project, doc)

    def test_standalone_page_reference_links_and_warning_projection_are_read_only(self):
        doc = self.standalone()
        before = review_path(self.project).read_bytes()
        markup = self.client.get('/structure').text
        self.assertIn('src="/source-page/13.png"', markup)
        self.assertIn('Source page 13 · No individual block assigned · Whole-page context', markup)
        self.assertIn('/source.pdf#page=13', markup)
        self.assertIn('not a confirmed infographic', markup)
        self.assertNotIn('Image preview unavailable', markup)
        self.assertIn('id="source-page-visual-reviews"', markup)
        self.assertEqual(_source_page_visual_reviews(doc, 14)['13'], [
            {'target': 'visual-page-check-13', 'label': 'Whole-page visual check: decision pending'}])
        accessibility = self.client.get('/accessibility').text
        self.assertIn('source_page=13#visual-page-check-13', accessibility)
        self.assertEqual(review_path(self.project).read_bytes(), before)

    def test_explicit_associated_image_wins_and_invalid_page_is_not_guessed(self):
        doc = self.standalone()
        asset = self.project / 'extraction/raw/images/associated.png'
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b'fixture image')
        doc['blocks'].append({'id': 'associated', 'type': 'image', 'src': 'extraction/raw/images/associated.png',
                              'alt': 'Saved alternative', 'provenance': {'source_page': 1}})
        visual = {'id': 'associated-description', 'source_page': 1, 'source_block_id': 'associated'}
        markup = _visual_reference(self.project, doc, visual)
        self.assertIn('associated.png', markup)
        self.assertIn('Block 4 · Associated image', markup)
        self.assertNotIn('src="/source-page/', markup)
        unknown = _visual_reference(self.project, doc, {'id': 'unknown', 'source_page': 999})
        self.assertIn('No associated image or valid source page', unknown)
        self.assertNotIn('<img', unknown)
        self.assertEqual(_source_page_visual_reviews(doc, None), {})

    def test_description_decision_refreshes_page_warning_and_preserves_block_approval(self):
        doc = self.standalone()
        before_blocks = copy.deepcopy(doc['blocks'])
        response = self.client.post('/api/complex-visuals/page-check-13', headers=self.headers(), json={
            'expected_review_token': review_token(doc), 'status': 'not_applicable'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn('13', response.json()['source_page_visual_reviews'])
        self.assertIn('13', response.json()['source_page_reviews'])
        current = ensure_review_document(self.project)
        self.assertEqual(current['blocks'], before_blocks)
        self.assertEqual(current['review']['complex_visuals'][0]['recovered_text'], 'Retained source words')
        self.assertEqual(current['review']['complex_visuals'][0]['status'], 'not_applicable')


if __name__ == '__main__':
    unittest.main()
