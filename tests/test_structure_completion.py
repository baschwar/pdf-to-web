from review_helpers import stamp_fixture_approvals, approve_publication_fixture
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
        document['review']['complex_visuals'][0]['accessibility']['short_alt'] = 'Synthetic chart summary'
        document['review']['complex_visuals'][0]['status'] = 'reviewed'
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)

    def completion_visible(self):
        return 'id="structure-review-complete"' in self.client.get('/structure').text

    def test_all_approved_show_message_and_accessibility_link(self):
        self.set_states(['approved'] * 5)
        page = self.client.get('/structure').text
        self.assertIn('Structure review complete', page)
        self.assertIn('href="/accessibility" role="button" class="review-approve">Continue to Accessibility', page)

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
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        self.assertFalse(self.completion_visible())

    def test_final_approval_shows_message_and_undo_removes_it(self):
        self.set_states(['approved', 'approved', 'needs_review', 'approved', 'approved'])
        update_block(self.root, 'photo', {'review_status': 'approved'})
        self.assertTrue(self.completion_visible())
        undo_last(self.root)
        self.assertFalse(self.completion_visible())

    def test_status_counts_separate_pending_from_reviewed(self):
        self.set_states(['approved', 'excluded', 'needs_review', 'unreviewed', 'approved'])
        page = self.client.get('/structure').text
        self.assertIn('Blocks reviewed 2 · Excluded 1 · Total 5 blocks', page)
        self.assertIn('Pending 2 review tasks', page)
        self.assertIn('2 block reviews · 0 description reviews', page)

    def test_accessibility_shows_live_results_and_diagnostic_block(self):
        document = ensure_review_document(self.root)
        document['review']['issues'] = [{'code': 'block_review_required', 'message': '1 block(s) require review before export.', 'block_ids': ['photo']}]
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        page = self.client.get('/accessibility').text
        self.assertNotIn('Generate accessibility report', page)
        self.assertNotIn('accessibility-export-result', page)
        self.assertIn('href="/help#review-counts"', page)
        self.assertIn('Required corrections cannot be waived.', page)
        self.assertIn('href="/structure?return_to=accessibility&amp;finding=diagnostic%3Ablock_review_required%3Adocument#block-photo"', page)
        self.assertIn('Recorded during extraction. Current block statuses:', page)
