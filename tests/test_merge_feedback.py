"""Mixed blocks never silently become a list or lose semantic content."""
import copy
import re
import unittest
import test_image_draft_routes as routes
from pdf_to_web.review_state import ensure_review_document, save_review_document, merge_with_next, undo_last, update_block


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
        self.assertIn('cannot join list containers or create a list from mixed blocks', screen)
        for identity in ('heading', 'steps'):
            result = self.client.post('/api/blocks/'+identity+'/merge', headers=self.headers, json={})
            self.assertEqual(result.status_code, 400)
            self.assertIn('cannot join list containers', result.json()['error'])
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
