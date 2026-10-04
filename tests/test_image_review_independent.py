"""Independent regression checks of a single image-owned review task."""
import copy
import unittest

import test_image_draft_routes as routes
import test_unified_image_review as existing
from pdf_to_web.accessibility import assess_document
from pdf_to_web.image_review import description_owner, descriptions_for, review_token
from pdf_to_web.publication import effective_block_status
from pdf_to_web.review_state import ensure_review_document, review_progress, save_review_document, undo_last, update_block


class IndependentImageReviewTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp
    model = existing.UnifiedImageReviewTests.model
    approve = existing.UnifiedImageReviewTests.approve
    batch = existing.UnifiedImageReviewTests.batch
    batch_payload = existing.UnifiedImageReviewTests.batch_payload

    def edit_payload(self, document, identity='image-2', **overrides):
        block = next(b for b in document['blocks'] if b['id'] == identity)
        edits = []
        for visual in descriptions_for(document, block):
            text = visual.get('accessibility', {})
            edits.append({'id': visual['id'], 'long_description': text.get('long_description', ''),
                          'adjacent_text': text.get('adjacent_text', ''), 'disposition': 'include',
                          'type': visual.get('type', ''), 'recovered_text': visual.get('recovered_text', ''),
                          'review_note': visual.get('review_note', '')})
        return {'alt': block['alt'], 'caption': block.get('caption', ''), 'decorative': bool(block.get('decorative')),
                'expected_review_token': review_token(document), 'description_edits': edits, **overrides}

    def test_pending_description_derives_one_image_task_without_rewriting_raw_approval(self):
        document = self.model(3)
        before = (self.root / 'review/current.json').read_bytes()
        block = document['blocks'][3]
        self.assertEqual(block['review']['status'], 'approved')
        self.assertEqual(effective_block_status(block, document), 'needs_review')
        progress = review_progress(document)
        self.assertEqual((progress['pending_tasks'], progress['pending_blocks'], progress['pending_descriptions'], progress['pending_images']), (1, 1, 1, 1))
        page = self.client.get('/structure').text
        self.assertRegex(page, r'id="block-image-2"[^>]*data-review-status="needs_review"')
        self.assertEqual(page.count('id="visual-description-2"'), 1)
        self.assertNotIn('class="complex-visual-form"', page)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_two_pending_descriptions_share_one_task_and_one_manual_approval(self):
        document = self.model(3)
        visual = copy.deepcopy(document['review']['complex_visuals'][2])
        visual['id'] = 'second-description'
        document['review']['complex_visuals'].append(visual)
        save_review_document(self.root, document)
        document = ensure_review_document(self.root)
        progress = review_progress(document)
        self.assertEqual((progress['pending_tasks'], progress['pending_descriptions'], progress['linked_pending_descriptions']), (1, 2, 2))
        self.assertEqual(self.approve().status_code, 200)
        reopened = ensure_review_document(self.root)
        self.assertEqual(review_progress(reopened)['pending_tasks'], 0)
        self.assertTrue(all(v['status'] == 'reviewed' for v in descriptions_for(reopened, reopened['blocks'][3])))
        undo_last(self.root)
        self.assertEqual(review_progress(ensure_review_document(self.root))['pending_tasks'], 1)

    def test_noop_full_form_and_reviewer_note_preserve_approved_material(self):
        self.model(3)
        self.assertEqual(self.approve().status_code, 200)
        document = ensure_review_document(self.root)
        payload = self.edit_payload(document)
        payload['description_edits'][0]['review_note'] = 'Human checked image purpose.'
        saved = update_block(self.root, 'image-2', payload)
        self.assertEqual(effective_block_status(saved['blocks'][3], saved), 'approved')
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'reviewed')
        self.assertEqual(saved['review']['complex_visuals'][2]['review_note'], 'Human checked image purpose.')
        self.assertEqual(review_progress(saved)['pending_tasks'], 0)

    def test_ordinary_full_form_save_cannot_review_complete_text(self):
        document = self.model(3)
        saved = update_block(self.root, 'image-2', self.edit_payload(document))
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'needs_text_equivalent')
        self.assertEqual(review_progress(saved)['pending_tasks'], 1)

    def test_caption_edit_invalidates_current_owner_and_description_and_undo_restores(self):
        self.model(3)
        self.assertEqual(self.approve().status_code, 200)
        before = ensure_review_document(self.root)
        saved = update_block(self.root, 'image-2', {'caption': 'A corrected caption.'})
        self.assertEqual(saved['blocks'][3]['review']['status'], 'needs_review')
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'reclassified')
        self.assertEqual(review_progress(saved)['pending_tasks'], 1)
        undo_last(self.root)
        reopened = ensure_review_document(self.root)
        self.assertEqual(reopened['blocks'], before['blocks'])
        self.assertEqual(reopened['review'], before['review'])

    def test_no_separate_description_is_explicit_single_combined_decision(self):
        document = self.model(3)
        payload = self.edit_payload(document)
        payload['description_edits'][0].update(long_description='', disposition='not_applicable')
        response = self.approve(**payload)
        self.assertEqual(response.status_code, 200, response.text)
        saved = ensure_review_document(self.root)
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'not_applicable')
        self.assertEqual(effective_block_status(saved['blocks'][3], saved), 'approved')
        self.assertEqual(review_progress(saved)['pending_tasks'], 0)
        undo_last(self.root)
        self.assertEqual(review_progress(ensure_review_document(self.root))['pending_tasks'], 1)

    def test_ordinary_save_of_description_disposition_does_not_create_decision(self):
        document = self.model(3)
        payload = self.edit_payload(document)
        payload['description_edits'][0]['disposition'] = 'not_applicable'
        saved = update_block(self.root, 'image-2', payload)
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'needs_text_equivalent')
        self.assertEqual(review_progress(saved)['pending_tasks'], 1)

    def test_standalone_description_retains_editor_and_separate_pending_task(self):
        document = self.model(2)
        document['review']['complex_visuals'].append({'id': 'standalone', 'type': 'chart', 'status': 'needs_text_equivalent',
                                                    'accessibility': {'short_alt': 'Chart overview', 'long_description': 'Complete chart explanation.'}})
        save_review_document(self.root, document)
        saved = ensure_review_document(self.root)
        visual = saved['review']['complex_visuals'][-1]
        self.assertIsNone(description_owner(saved, visual))
        self.assertEqual((review_progress(saved)['pending_tasks'], review_progress(saved)['standalone_pending_descriptions']), (1, 1))
        page = self.client.get('/structure').text
        self.assertIn('Standalone visual descriptions', page)
        self.assertIn('id="visual-standalone"', page)

    def test_invalid_association_does_not_own_or_approve_hidden_description(self):
        document = self.model(3)
        document['review']['complex_visuals'][2]['source_block_id'] = 'image-1'
        save_review_document(self.root, document)
        saved = ensure_review_document(self.root)
        self.assertIsNone(description_owner(saved, saved['review']['complex_visuals'][2]))
        before = (self.root / 'review/current.json').read_bytes()
        self.assertEqual(self.approve().status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_stale_bulk_snapshot_rejects_entire_selection_without_another_revision(self):
        self.model(4)
        payload = self.batch_payload(['block:image-2', 'block:image-3'], status='approved', classification='Blocks · image')
        update_block(self.root, 'image-3', {'caption': 'Concurrent author correction.'})
        before = (self.root / 'review/current.json').read_bytes()
        response = self.batch(payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_description_pending_does_not_duplicate_accessibility_structure_finding(self):
        document = self.model(3)
        items = assess_document(document)['items']
        descriptions = [i for i in items if i.get('visual_id') == 'description-2']
        structural = [i for i in items if i.get('block_id') == 'image-2' and i.get('category') == 'structure']
        self.assertTrue(descriptions)
        self.assertEqual(structural, [])
