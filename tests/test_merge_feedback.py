"""Mixed blocks never silently become a list or lose semantic content."""
import copy
import re
import unittest
import test_image_draft_routes as routes
from pdf_to_web.review_state import ensure_review_document, save_review_document, merge_with_next, undo_last, update_block
from pdf_to_web.image_review import review_token


class MergeFeedbackTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def document(self, blocks):
        document = ensure_review_document(self.root)
        document['blocks'] = blocks
        document['review']['complex_visuals'] = []
        document['review']['issues'] = []
        document.pop('output_pages', None)
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def test_mixed_sequence_has_disabled_merge_with_reason_and_unchanged_rejection(self):
        blocks = [{'id': 'heading', 'type': 'heading', 'level': 2, 'content': 'Instructions'},
                  {'id': 'steps', 'type': 'list', 'children': [{'id': 'item', 'type': 'list_item', 'content': 'Existing step'}]},
                  {'id': 'paragraph', 'type': 'paragraph', 'content': 'Additional information'}]
        self.document(blocks)
        before = (self.root / 'review/current.json').read_bytes()
        screen = self.client.get('/structure').text
        for identity in ('heading', 'steps', 'paragraph'):
            card = screen.split('id="block-' + identity + '"')[1].split('</article>')[0]
            self.assertRegex(card, r'data-action="merge"[^>]+disabled aria-describedby="merge-help-')
        self.assertIn('List blocks cannot be merged here', screen)
        for identity in ('heading', 'steps'):
            result = self.client.post('/api/blocks/'+identity+'/merge', headers=self.headers, json={})
            self.assertEqual(result.status_code, 400)
            self.assertIn('List blocks cannot be merged here', result.json()['error'])
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_supported_pairs_share_enabled_controls_and_preserve_other_approved_blocks(self):
        for kind in ('paragraph', 'heading', 'quote', 'caption', 'callout', 'unknown'):
            with self.subTest(kind=kind):
                pair = [{'id': identity, 'type': kind, 'level': 2, 'content': identity,
                         'review': {'status': 'approved'}} for identity in ('first', 'second', 'other')]
                document = self.document(pair)
                before_other = copy.deepcopy(document['blocks'][2])
                screen = self.client.get('/structure').text
                card = screen.split('id="block-first"')[1].split('</article>')[0]
                button = re.search(r'<button[^>]+data-action="merge"[^>]*>', card).group()
                self.assertNotIn(' disabled', button)
                self.assertIn('data-next-block-id="second"', button)
                self.assertIn('aria-describedby="merge-help-first"', button)
                token = review_token(ensure_review_document(self.root))
                response = self.client.post('/api/blocks/first/merge', headers=self.headers,
                    json={'expected_review_token': token, 'expected_next_block_id': 'second'})
                self.assertEqual(response.status_code, 200, response.text)
                current = ensure_review_document(self.root)
                self.assertEqual(current['blocks'][0]['content'], 'first\n\nsecond')
                self.assertEqual(current['blocks'][0]['review']['status'], 'needs_review')
                self.assertEqual(current['blocks'][1], before_other)
                undo_last(self.root)
                self.assertEqual(ensure_review_document(self.root)['blocks'], document['blocks'])

    def test_last_excluded_heading_and_list_boundaries_reject_without_history_changes(self):
        first = {'id': 'first', 'type': 'paragraph', 'content': 'First', 'review': {'status': 'approved'}}
        second = {'id': 'second', 'type': 'paragraph', 'content': 'Second', 'review': {'status': 'approved'}}
        variants = [
            ([first], 'no following block'),
            ([first, {**second, 'review': {'status': 'excluded'}}], 'excluded content'),
            ([{**first, 'excluded': True}, second], 'excluded content'),
            ([{**first, 'type': 'heading', 'level': 1}, {**second, 'type': 'heading', 'level': 2}], 'different levels'),
            ([{**first, 'type': 'list', 'children': [{'id': 'one', 'type': 'list_item', 'content': 'One'}]}, second], 'List blocks'),
            ([first, {**second, 'type': 'list', 'children': [{'id': 'two', 'type': 'list_item', 'content': 'Two'}]}], 'List blocks'),
        ]
        for blocks, reason in variants:
            with self.subTest(reason=reason, blocks=blocks):
                self.document(copy.deepcopy(blocks))
                self.client.get('/structure')
                before = {str(p.relative_to(self.root)): p.read_bytes()
                          for p in (self.root / 'review').rglob('*.json')}
                response = self.client.post('/api/blocks/first/merge', headers=self.headers, json={})
                self.assertEqual(response.status_code, 400)
                self.assertIn(reason, response.json()['error'])
                after = {str(p.relative_to(self.root)): p.read_bytes()
                         for p in (self.root / 'review').rglob('*.json')}
                self.assertEqual(after, before)

    def test_filtered_screen_keeps_actual_next_list_candidate_and_its_disabled_reason(self):
        self.document([{'id': 'first', 'type': 'paragraph', 'content': 'First'},
                       {'id': 'hidden', 'type': 'list', 'children': [{'id': 'item', 'type': 'list_item', 'content': 'Keep'}],
                        'review': {'status': 'approved'}},
                       {'id': 'later', 'type': 'paragraph', 'content': 'Later'}])
        screen = self.client.get('/structure').text
        card = screen.split('id="block-first"')[1].split('</article>')[0]
        self.assertRegex(card, r'data-action="merge"[^>]+data-next-block-id="hidden"[^>]+disabled')
        self.assertIn('List blocks cannot be merged here', card)

    def test_changed_snapshot_or_next_candidate_rejects_without_overwriting_new_decisions(self):
        self.document([{'id': 'first', 'type': 'paragraph', 'content': 'First'},
                       {'id': 'second', 'type': 'paragraph', 'content': 'Second'}])
        old_token = review_token(ensure_review_document(self.root))
        update_block(self.root, 'second', {'review_status': 'approved'})
        current = ensure_review_document(self.root)
        before = (self.root / 'review/current.json').read_bytes()
        for token, target, reason in [(old_token, 'second', 'document changed'),
                                     (review_token(current), 'wrong', 'next block changed')]:
            with self.subTest(reason=reason):
                response = self.client.post('/api/blocks/first/merge', headers=self.headers,
                    json={'expected_review_token': token, 'expected_next_block_id': target})
                self.assertEqual(response.status_code, 400)
                self.assertIn(reason, response.json()['error'])
                self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_rich_notes_nested_and_excluded_text_reject_without_losing_identity_or_metadata(self):
        for protected in ({'runs': [{'type': 'link', 'text': 'First', 'url': 'https://example.test'}]},
                          {'footnote_references': [{'id': 'citation', 'note_id': 'note'}]},
                          {'children': [{'id': 'nested', 'type': 'paragraph', 'content': 'Nested text'}]},
                          {'review': {'status': 'excluded'}}):
            with self.subTest(protected=protected):
                first = {'id': 'first', 'type': 'paragraph', 'content': 'First', **copy.deepcopy(protected)}
                self.document([first, {'id': 'second', 'type': 'paragraph', 'content': 'Second'}])
                before = (self.root / 'review/current.json').read_bytes()
                with self.assertRaises(ValueError):
                    merge_with_next(self.root, 'first')
                self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_plain_text_merge_requires_fresh_approval_and_undo_restores_source_blocks(self):
        before = self.document([{'id': 'first', 'type': 'paragraph', 'content': 'First', 'provenance': {'source_page': 1}},
                                {'id': 'second', 'type': 'paragraph', 'content': 'Second', 'provenance': {'source_page': 2}}])
        update_block(self.root, 'first', {'review_status': 'approved'})
        approved = ensure_review_document(self.root)
        current = merge_with_next(self.root, 'first')
        self.assertEqual(current['blocks'][0]['id'], 'first')
        self.assertEqual(current['blocks'][0]['content'], 'First\n\nSecond')
        self.assertEqual(current['blocks'][0]['review']['status'], 'needs_review')
        self.assertIn(2, current['blocks'][0]['provenance']['merged_source_pages'])
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], approved['blocks'])

    def test_supported_merge_preserves_both_footnote_positions_and_backlinks(self):
        from pdf_to_web.exporters import html
        document = self.document([
            {'id': 'first', 'type': 'paragraph', 'content': 'Intro1', 'footnote_references': [{'id': 'ref1', 'footnote_id': 'note1', 'marker': '1', 'start': 5, 'end': 6}]},
            {'id': 'second', 'type': 'paragraph', 'content': ' Next2', 'footnote_references': [{'id': 'ref2', 'footnote_id': 'note2', 'marker': '2', 'start': 5, 'end': 6}]},
        ])
        document['footnotes'] = [
            {'id': 'note1', 'marker': '1', 'text': 'First note', 'references': [{'id': 'ref1', 'block_id': 'first'}]},
            {'id': 'note2', 'marker': '2', 'text': 'Second note', 'references': [{'id': 'ref2', 'block_id': 'second'}]},
        ]
        save_review_document(self.root, document)
        before = ensure_review_document(self.root)
        current = merge_with_next(self.root, 'first')
        references = current['blocks'][0]['footnote_references']
        self.assertEqual([(r['id'], r['start'], r['end']) for r in references], [('ref1', 5, 6), ('ref2', 12, 13)])
        self.assertEqual(current['footnotes'][1]['references'][0]['block_id'], 'first')
        rendered = html.render_document(current)
        for identity in ('ref1', 'ref2', 'note1', 'note2'):
            self.assertIn('id="' + identity + '"', rendered)
        self.assertIn('href="#ref2"', rendered)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])
        self.assertEqual(ensure_review_document(self.root)['footnotes'], before['footnotes'])
