import unittest
import test_image_draft_routes as routes
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, undo_last


class StructureCompletionTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def set_states(self, states, *, status='review_ready'):
        document = ensure_review_document(self.root)
        document['review']['status'] = status
        for block, state in zip(document['blocks'], states):
            if state == 'approved' and block.get('type') == 'image' and not block.get('decorative') and not block.get('alt'):
                block['alt'] = 'Synthetic reviewed alternative'
            block.setdefault('review', {})['status'] = state
        save_review_document(self.root, document)

    def completion_visible(self):
        return 'id="structure-review-complete"' in self.client.get('/structure').text

    def test_all_approved_show_message_and_accessibility_link(self):
        self.set_states(['approved'] * 5)
        page = self.client.get('/structure').text
        self.assertIn('All blocks have been reviewed', page)
        self.assertIn('href="/accessibility" role="button">Continue to Accessibility', page)

    def test_excluded_blocks_count_as_resolved_decisions(self):
        self.set_states(['approved', 'excluded', 'approved', 'excluded', 'approved'])
        self.assertTrue(self.completion_visible())

    def test_needs_review_is_not_completion_even_when_progress_counts_it(self):
        self.set_states(['approved', 'approved', 'needs_review', 'approved', 'approved'])
        self.assertFalse(self.completion_visible())
        self.set_states(['approved', 'approved', 'unreviewed', 'approved', 'approved'])
        self.assertFalse(self.completion_visible())

    def test_empty_and_blocked_documents_do_not_claim_completion(self):
        self.set_states(['approved'] * 5, status='conversion_blocked')
        self.assertFalse(self.completion_visible())
        document = ensure_review_document(self.root)
        document['review']['status'] = 'review_ready'; document['blocks'] = []
        save_review_document(self.root, document)
        self.assertFalse(self.completion_visible())

    def test_final_approval_shows_message_and_undo_removes_it(self):
        self.set_states(['approved', 'approved', 'needs_review', 'approved', 'approved'])
        update_block(self.root, 'photo', {'review_status': 'approved'})
        self.assertTrue(self.completion_visible())
        undo_last(self.root)
        self.assertFalse(self.completion_visible())
