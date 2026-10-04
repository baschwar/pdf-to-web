"""Useful drafting defaults and a discoverable existing CSV workflow."""
import unittest

import test_export_media_journey_independent as fixtures
from pdf_to_web.review_state import save_review_document


class HeldWorkflowDiscoveryTests(unittest.TestCase):
    setUp = fixtures.IndependentExportMediaJourneyTests.setUp
    model = fixtures.IndependentExportMediaJourneyTests.model
    image_model = fixtures.IndependentExportMediaJourneyTests.image_model
    prepare = fixtures.IndependentExportMediaJourneyTests.prepare

    def test_drafting_is_open_for_pending_image_work_without_saving_or_approval(self):
        document = self.model(3)
        document['review']['complex_visuals'][0]['status'] = 'needs_text_equivalent'
        save_review_document(self.root, document)
        before = (self.root / 'review/current.json').read_bytes()
        page = self.client.get('/structure').text
        self.assertIn('id="image-description-tools" class="review-tools" open', page)
        self.assertLess(page.index('id="image-description-tools"'), page.index('id="blocks-heading"'))
        self.assertIn('Drafting is optional', page)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_ready_images_without_requests_stay_compact_but_existing_requests_are_useful(self):
        document = self.model(2)
        page = self.client.get('/structure').text
        self.assertNotIn('id="image-description-tools" class="review-tools" open', page)
        result = self.client.post('/api/image-drafts/export', headers=self.headers,
            json={'document_id': document['output_pages']['project_id'], 'block_ids': ['image-0']})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertIn('id="image-description-tools" class="review-tools" open', self.client.get('/structure').text)

    def test_manual_entry_precedes_xml_and_download_is_available_only_after_preparation(self):
        self.model(2)
        before = (self.root / 'review/current.json').read_bytes()
        page = self.client.get('/export').text
        self.assertLess(page.index('id="open-manual-media"'), page.index('id="media-wxr-form"'))
        self.assertEqual(page.count('id="media-mapping-form"'), 1)
        self.assertIn('id="manual-media-tools"', page)
        self.assertIn('keep block_id and asset_filename unchanged', page)
        self.assertIn('download hidden>Save browser copy of current mapping CSV', page)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertEqual(self.prepare().status_code, 200)
        page = self.client.get('/export').text
        self.assertIn('download>Save browser copy of current mapping CSV', page)


if __name__ == '__main__':
    unittest.main()
