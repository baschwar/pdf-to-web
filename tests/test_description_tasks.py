"""Description tasks retain distinct counts, identities, reasons and decisions."""
import copy
import re
import unittest

import test_image_draft_routes as routes
from review_helpers import stamp_fixture_approvals
from pdf_to_web.accessibility import visual_readiness
from pdf_to_web.publication import readiness_findings
from pdf_to_web.review_state import (
    ensure_review_document, review_progress, save_review_document, undo_last,
    update_block, update_complex_visual,
)


class DescriptionTaskTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def task_document(self):
        document = ensure_review_document(self.root)
        document['blocks'] = [{'id': 'title', 'type': 'heading', 'level': 1, 'content': 'Synthetic guide'}]
        document['review']['complex_visuals'] = []
        for index in range(5):
            identity = f'image-{index}'
            visual_id = f'description-{index}'
            document['blocks'].append({'id': identity, 'type': 'image', 'src': 'images/photo.png',
                                       'alt': f'Image purpose {index}', 'complex_visual_id': visual_id,
                                       'provenance': {'source_page': 1}})
            document['review']['complex_visuals'].append({
                'id': visual_id, 'source_block_id': identity, 'source_page': 1,
                'status': 'reclassified', 'accessibility': {'short_alt': f'Image purpose {index}', 'long_description': f'Long equivalent {index}'},
            })
        document['blocks'].extend({'id': f'paragraph-{index}', 'type': 'paragraph', 'content': f'Resource {index}'} for index in range(48))
        for block in document['blocks']:
            block['review'] = {'status': 'approved'}
        stamp_fixture_approvals(document)
        document.pop('output_pages', None)
        save_review_document(self.root, document, snapshot=False)
        return ensure_review_document(self.root)

    def test_54_blocks_and_five_description_tasks_on_every_document_page(self):
        document = self.task_document()
        progress = review_progress(document)
        self.assertEqual((progress['approved'], progress['total']), (49, 54))
        self.assertEqual((progress['pending_blocks'], progress['pending_descriptions'], progress['pending_tasks']), (5, 5, 5))
        self.assertEqual(progress['description_total'], 5)
        self.assertEqual(len(readiness_findings(document)), 5)
        for route in ('/document', '/structure', '/accessibility', '/output-pages', '/preview', '/export'):
            with self.subTest(route=route):
                page = self.client.get(route).text
                self.assertEqual(page.count('id="review-summary"'), 1)
                self.assertEqual(page.count('Pending 5 review tasks'), 1)
                self.assertIn('Blocks reviewed 49 · Excluded 0 · Total 54 blocks', page)
                self.assertIn('5 image reviews · 0 other block reviews · 5 description reviews included in the image reviews; 0 standalone description reviews', page)
                self.assertNotIn('Pending 0', page)
                self.assertNotIn('Total 59', page)
                self.assertNotIn('id="structure-review-complete"', page)

    def test_mixed_tasks_and_description_exceptions_keep_units(self):
        document = self.task_document()
        document['blocks'][-1]['review']['status'] = 'needs_review'
        visuals = document['review']['complex_visuals']
        visuals[0]['status'] = 'reviewed'
        visuals[1]['status'] = 'not_applicable'
        visuals[2]['status'] = 'excluded'
        document['blocks'][4]['decorative'] = True
        document['blocks'][5]['review']['status'] = 'excluded'
        stamp_fixture_approvals(document)
        progress = review_progress(document)
        self.assertEqual((progress['pending_blocks'], progress['pending_descriptions'], progress['pending_tasks']), (1, 0, 1))
        self.assertEqual(progress['total'], 54)

    def test_reclassified_timestamp_does_not_claim_prior_approval(self):
        document = self.task_document()
        visual = document['review']['complex_visuals'][0]
        visual['reviewed_at'] = '2026-10-01T10:00:00Z'
        readiness = visual_readiness(document, visual)
        self.assertEqual(readiness['reason_code'], 'reclassified_pending')
        self.assertNotIn('Changed', readiness['reason'])
        self.assertIn('Save and approve once', readiness['action'])
        self.assertIn('No separate description needed', readiness['action'])

    def test_exact_card_has_context_and_one_status_with_accessible_reason(self):
        self.task_document()
        page = self.client.get('/structure').text
        card = page.split('id="visual-description-0"')[1].split('</article>')[0]
        self.assertEqual(card.count('Text provided; awaiting manual review'), 1)
        self.assertIn('aria-labelledby="visual-description-0-heading"', card)
        self.assertIn('visual-description-0-reason visual-description-0-action', card)
        self.assertIn('Image purpose 0', page.split('id="block-image-0"')[1].split('</article>')[0])
        self.assertEqual(page.count('id="visual-description-0"'), 1)
        self.assertNotIn('Text recovery Unknown', card)
        document_page = self.client.get('/document').text
        links = re.findall(r'<a href="/structure#visual-description-\d">([^<]+)</a>', document_page)
        self.assertEqual(len(links), 0)  # Linked records belong to their image review.
        self.assertNotIn('>Review descriptions</a>', document_page)

    def test_manual_decision_updates_api_counts_and_undo_restores(self):
        before = self.task_document()
        response = self.client.post('/api/complex-visuals/description-0', headers=self.headers, json={'status': 'reviewed'})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data['progress']['pending_tasks'], 4)
        self.assertIn('Pending 4 review tasks', data['review_summary_html'])
        self.assertEqual(data['visual']['reason'], '')
        self.assertEqual(data['visual']['action'], '')
        undo_last(self.root)
        restored = ensure_review_document(self.root)
        self.assertEqual(restored['blocks'], before['blocks'])
        self.assertEqual(restored['review']['complex_visuals'], before['review']['complex_visuals'])
        self.assertEqual(review_progress(restored)['pending_tasks'], 5)

    def test_evidenced_edit_reason_survives_reopen_and_clears_on_fresh_review(self):
        self.task_document()
        update_complex_visual(self.root, 'description-0', {'status': 'reviewed'})
        reviewed = copy.deepcopy(ensure_review_document(self.root))
        update_complex_visual(self.root, 'description-0', {'long_description': 'Changed reviewed equivalent', 'status': 'reviewed'})
        edited = ensure_review_document(self.root)
        visual = edited['review']['complex_visuals'][0]
        self.assertEqual(visual['status'], 'reclassified')
        self.assertEqual(visual['review_change_fields'], ['long_description'])
        self.assertEqual(visual_readiness(edited, visual)['reason'], 'Changed since Reviewed: long description.')
        self.assertEqual(ensure_review_document(self.root)['review']['complex_visuals'][0], visual)
        update_complex_visual(self.root, 'description-0', {'status': 'reviewed'})
        fresh = ensure_review_document(self.root)['review']['complex_visuals'][0]
        self.assertNotIn('review_reason', fresh)
        self.assertNotIn('review_change_fields', fresh)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['review']['complex_visuals'][0], visual)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['review']['complex_visuals'][0], reviewed['review']['complex_visuals'][0])

    def test_ordinary_image_description_save_records_only_actual_changed_field(self):
        self.task_document()
        update_complex_visual(self.root, 'description-0', {'status': 'reviewed'})
        update_block(self.root, 'image-0', {'long_description': 'Image-editor change'})
        document = ensure_review_document(self.root)
        visual = document['review']['complex_visuals'][0]
        self.assertEqual(visual['review_reason'], 'changed_after_approval')
        self.assertEqual(visual['review_change_fields'], ['long_description'])

    def test_noop_legacy_short_alt_fallback_and_note_do_not_invalidate_review(self):
        document = self.task_document()
        visual = document['review']['complex_visuals'][0]
        visual['status'] = 'reviewed'
        visual['accessibility'].pop('short_alt')
        save_review_document(self.root, document, snapshot=False)
        update_complex_visual(self.root, 'description-0', {'status': 'reviewed', 'short_alt': 'Image purpose 0', 'review_note': 'Same text; reviewer note only'})
        document = ensure_review_document(self.root)
        visual = document['review']['complex_visuals'][0]
        self.assertEqual(visual['status'], 'reviewed')
        self.assertNotIn('review_reason', visual)
        self.assertEqual(document['blocks'][1]['review']['status'], 'approved')

    def test_export_has_one_target_per_task_with_all_required_guidance(self):
        document = self.task_document()
        document['blocks'][1]['alt'] = ''
        document['blocks'][1]['review']['status'] = 'needs_review'
        save_review_document(self.root, document, snapshot=False)
        page = self.client.get('/export').text
        readiness = page.split('<section aria-labelledby="readiness-heading">')[1].split('</section>')[0]
        self.assertEqual(readiness.count('href="/structure#block-image-0"'), 1)
        for index in range(5):
            self.assertEqual(readiness.count(f'href="/structure#visual-description-{index}"'), 1)
        self.assertIn('Add alt text or mark this image decorative.', page)
        self.assertIn('Save and approve once', page)
        self.assertNotIn('Blocks needing review</h3>', page)
        self.assertNotIn('Descriptions needing attention</h3>', page)
        self.assertIn('href="/help#title-export"', page)
        self.assertIn('standalone file retains one H1', self.client.get('/help').text)

    def test_complete_and_blocked_states_show_status_once(self):
        self.task_document()
        for index in range(5):
            update_complex_visual(self.root, f'description-{index}', {'status': 'reviewed'})
        for route in ('/document', '/structure'):
            page = self.client.get(route).text
            self.assertEqual(page.count('>Structure review complete</h2>'), 1)
            if route == '/document':
                self.assertNotIn('<strong>Structure reviewed</strong>', page)
            else:
                self.assertIn('class="review-overall-status" hidden', page)
        document = ensure_review_document(self.root)
        document['review']['status'] = 'conversion_blocked'
        save_review_document(self.root, document, snapshot=False)
        page = self.client.get('/document').text
        self.assertEqual(page.count('<strong>Conversion blocked</strong>'), 1)
        self.assertNotIn('id="document-status-heading"', page)
