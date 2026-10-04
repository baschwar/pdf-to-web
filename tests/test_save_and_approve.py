"""Explicit combined approval saves final author edits atomically with Undo."""
import copy
import unittest
from unittest.mock import patch

import test_list_content_recovery as recovery
from pdf_to_web.export import export_project
from pdf_to_web.publication import content_digest, effective_block_status
from pdf_to_web.review_state import ensure_review_document, update_block, undo_last


class SaveAndApproveTests(unittest.TestCase):
    setUp = recovery.ListContentRecoveryTests.setUp
    document = recovery.ListContentRecoveryTests.document
    malformed = recovery.ListContentRecoveryTests.malformed

    def post(self, identity, changes):
        from pdf_to_web.image_review import review_token, descriptions_for
        document = ensure_review_document(self.root)
        block = next((b for b in document['blocks'] if str(b['id']) == identity), {})
        if block.get('type') == 'image':
            changes = {'expected_review_token': review_token(document), 'displayed_description_ids': [str(v['id']) for v in descriptions_for(document, block)], **changes}
        return self.client.post(f'/api/blocks/{identity}/save-and-approve', headers=self.headers, json=changes)

    def test_recovery_and_approval_are_one_revision_with_rich_exports_and_undo(self):
        before = self.document(self.malformed())
        original = (self.root / 'extraction/normalized/document.json').read_bytes()
        result = self.post('retained', {'content': 'Read the guide carefully.'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['block_status'], 'approved')
        after = ensure_review_document(self.root)
        block = after['blocks'][0]
        self.assertEqual(block['id'], 'retained')
        self.assertEqual(effective_block_status(block), 'approved')
        self.assertEqual(block['review']['content_sha256'], content_digest(block))
        self.assertEqual(block['children'][0]['runs'], before['blocks'][0]['runs'])
        self.assertEqual(block['children'][0]['provenance']['bounding_box'], [10, 20, 300, 40])
        self.assertEqual(after['review_session']['revision'], before['review_session']['revision'] + 1)
        paths = export_project(self.root, 'all')
        semantic = next(path for path in paths if path.suffix == '.html' and path.parent.name == 'html').read_text()
        self.assertIn('<strong>Read </strong>', semantic)
        self.assertIn('href="https://example.test/guide"', semantic)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])
        self.assertEqual((self.root / 'extraction/normalized/document.json').read_bytes(), original)

    def test_ordinary_save_still_requires_review_but_combined_save_stamps_final_text(self):
        self.document({'id': 'text', 'type': 'heading', 'level': 2, 'content': 'Before', 'review': {'status': 'approved'}})
        saved = update_block(self.root, 'text', {'content': 'Ordinary save', 'review_status': 'approved'})
        self.assertEqual(effective_block_status(saved['blocks'][0]), 'needs_review')
        before = copy.deepcopy(saved['blocks'])
        result = self.post('text', {'type': 'heading', 'level': 3, 'content': 'Combined save'})
        self.assertEqual(result.status_code, 200, result.text)
        block = ensure_review_document(self.root)['blocks'][0]
        self.assertEqual((block['content'], block['level']), ('Combined save', 3))
        self.assertEqual(effective_block_status(block), 'approved')
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before)

    def test_invalid_combined_save_does_not_save_content_or_approval(self):
        for block, changes in [
            (self.malformed(), {'content': ''}),
            ({'id': 'retained', 'type': 'image', 'alt': 'Original', 'caption': 'Before'}, {'alt': '', 'caption': 'Unsaved'}),
            ({'id': 'retained', 'type': 'list', 'children': [self.malformed()]}, {}),
        ]:
            with self.subTest(type=block['type']):
                self.document(block)
                current = (self.root / 'review/current.json').read_bytes()
                snapshots = set((self.root / 'review/revisions').glob('*.json'))
                response = self.post('retained', changes)
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual((self.root / 'review/current.json').read_bytes(), current)
                self.assertEqual(set((self.root / 'review/revisions').glob('*.json')), snapshots)

    def test_image_and_table_editors_save_fields_before_approval(self):
        for block, changes in [
            ({'id': 'edited', 'type': 'image', 'alt': '', 'caption': 'Before'}, {'alt': 'Informative image', 'caption': 'After'}),
            ({'id': 'edited', 'type': 'image', 'alt': 'Before'}, {'decorative': True}),
            ({'id': 'edited', 'type': 'table', 'rows': [[{'content': 'Header'}]]}, {'table_caption': 'Results', 'table_reviewed': True, 'table_header_row': True}),
        ]:
            with self.subTest(type=block['type'], changes=changes):
                self.document(block)
                response = self.post('edited', changes)
                self.assertEqual(response.status_code, 200, response.text)
                saved = ensure_review_document(self.root)['blocks'][0]
                self.assertEqual(effective_block_status(saved), 'approved')
                if block['type'] == 'table':
                    self.assertEqual(saved['caption'], 'Results')
                    self.assertTrue(saved['table_accessibility']['reviewed'])
                elif changes.get('decorative'):
                    self.assertEqual(saved['alt'], '')
                else:
                    self.assertEqual((saved['alt'], saved['caption']), ('Informative image', 'After'))

    def test_write_failure_rolls_back_combined_content_and_approval(self):
        self.document({'id': 'text', 'type': 'paragraph', 'content': 'Before'})
        before = (self.root / 'review/current.json').read_bytes()
        snapshots = set((self.root / 'review/revisions').glob('*.json'))
        with patch('pdf_to_web.review_state.save_project', side_effect=OSError('Cannot save project')):
            response = self.post('text', {'content': 'After'})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertEqual(set((self.root / 'review/revisions').glob('*.json')), snapshots)

    def test_combined_approval_keeps_page_assignments_but_invalidates_page_review(self):
        from pdf_to_web.review_state import save_review_document
        self.document({'id': 'text', 'type': 'paragraph', 'content': 'Before'})
        document = ensure_review_document(self.root)
        page = document['output_pages']['pages'][0]
        page['approval']['status'] = 'reviewed'
        save_review_document(self.root, document)
        before = ensure_review_document(self.root)
        response = self.post('text', {'content': 'After'})
        self.assertEqual(response.status_code, 200, response.text)
        after = ensure_review_document(self.root)
        self.assertEqual(after['output_pages']['pages'][0]['block_ids'], page['block_ids'])
        self.assertEqual(after['output_pages']['pages'][0]['id'], page['id'])
        self.assertEqual(after['output_pages']['pages'][0]['approval']['status'], 'needs_review')
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['output_pages'], before['output_pages'])

    def test_image_approval_also_approves_the_explicitly_displayed_description(self):
        from pdf_to_web.review_state import save_review_document
        self.document({'id': 'photo', 'type': 'image', 'alt': 'Before', 'complex_visual_id': 'visual'})
        document = ensure_review_document(self.root)
        document['review']['complex_visuals'] = [{'id': 'visual', 'type': 'image', 'source_block_id': 'photo',
            'status': 'reviewed', 'accessibility': {'short_alt': 'Before', 'long_description': 'Before description'}}]
        save_review_document(self.root, document)
        response = self.post('photo', {'alt': 'After', 'long_description': 'After description'})
        self.assertEqual(response.status_code, 200, response.text)
        after = ensure_review_document(self.root)
        self.assertEqual(effective_block_status(after['blocks'][0]), 'approved')
        self.assertEqual(after['review']['complex_visuals'][0]['status'], 'reviewed')

    def test_combined_action_preserves_authentication_and_conversion_block(self):
        before = (self.root / 'review/current.json').read_bytes()
        self.assertEqual(self.client.post('/api/blocks/p/save-and-approve', json={'content': 'After'}).status_code, 403)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.document({'id': 'text', 'type': 'paragraph', 'content': 'Before'})
        from pdf_to_web.review_state import save_review_document
        document = ensure_review_document(self.root)
        document['review']['status'] = 'conversion_blocked'
        save_review_document(self.root, document)
        before = (self.root / 'review/current.json').read_bytes()
        self.assertEqual(self.post('text', {'content': 'After'}).status_code, 409)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertNotIn('data-save-and-approve', self.client.get('/structure').text)

    def test_primary_editors_have_labeled_combined_action_including_nested_lists(self):
        blocks = [
            {'id': 'edited', 'type': 'paragraph', 'content': 'Text'},
            {'id': 'edited', 'type': 'image', 'alt': 'Image'},
            {'id': 'edited', 'type': 'table', 'rows': []},
            {'id': 'edited', 'type': 'list', 'children': [{'id': 'child', 'type': 'list_item', 'content': 'Item', 'children': [{'id': 'nested', 'type': 'paragraph', 'content': 'Note'}]}]},
        ]
        for block in blocks:
            with self.subTest(type=block['type']):
                self.document(block)
                page = self.client.get('/structure').text
                self.assertEqual(page.count('data-save-and-approve'), 1)
                self.assertIn('aria-label="Save and approve block 1"', page)
