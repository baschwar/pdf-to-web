import copy
import re
import unittest
from html.parser import HTMLParser

import test_image_draft_routes as routes
from pdf_to_web.image_review import review_token
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, undo_last


class FilterScreen(HTMLParser):
    def __init__(self, screen):
        super().__init__()
        self.cards = {}
        self.links = {}
        self.attrs = {}
        self.current_link = None
        self.feed(screen)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            self.attrs[values['id']] = values
        if tag == 'article' and 'block-card' in values.get('class', '').split():
            self.cards[values['id']] = values
        if tag == 'a' and ('data-filter' in values or 'data-type-filter' in values):
            self.current_link = ('review' if 'data-filter' in values else 'type', values.get('data-filter') or values['data-type-filter'])
            self.links[self.current_link] = ''

    def handle_data(self, value):
        if self.current_link:
            self.links[self.current_link] += value

    def handle_endtag(self, tag):
        if tag == 'a':
            self.current_link = None


class StructureFilterTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def document(self):
        document = ensure_review_document(self.root)
        document['blocks'] = [
            {'id': 'heading', 'type': 'heading', 'level': 1, 'content': 'Title'},
            {'id': 'paragraph', 'type': 'paragraph', 'content': 'Retained paragraph', 'review': {'status': 'approved'},
             'provenance': {'source_page': 1, 'bounding_box': [1, 2, 30, 40]}},
            {'id': 'list', 'type': 'list', 'children': [{'id': 'item', 'type': 'list_item', 'content': 'One',
              'children': [{'id': 'nested', 'type': 'paragraph', 'content': 'Nested text'}]}]},
            {'id': 'photo', 'type': 'image', 'src': 'images/photo.png', 'alt': 'Alt', 'review': {'status': 'approved'}},
            {'id': 'table', 'type': 'table', 'rows': [['Label', 'Value']]},
            *[{'id': kind, 'type': kind, 'content': kind} for kind in ('quote', 'caption', 'callout', 'unknown')],
        ]
        document['review']['complex_visuals'] = [{'id': 'description', 'source_block_id': 'photo', 'type': 'chart',
            'status': 'needs_text_equivalent', 'accessibility': {'long_description': 'Authored equivalent'}}]
        document['review']['issues'] = []
        document.pop('output_pages', None)
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def test_type_groups_count_only_top_level_blocks_and_pending_image_once(self):
        self.document()
        parsed = FilterScreen(self.client.get('/structure').text)
        self.assertEqual(len(parsed.cards), 9)
        self.assertEqual({k: v['data-filter-type'] for k, v in parsed.cards.items()}, {
            'block-heading': 'heading', 'block-paragraph': 'paragraph', 'block-list': 'list',
            'block-photo': 'image', 'block-table': 'table',
            **{'block-' + kind: 'other' for kind in ('quote', 'caption', 'callout', 'unknown')}})
        for kind, label, count in [('all', 'All types', 9), ('heading', 'Headings', 1), ('paragraph', 'Paragraphs', 1),
                                   ('list', 'Lists', 1), ('image', 'Images', 1), ('table', 'Tables', 1), ('other', 'Other', 4)]:
            self.assertEqual(parsed.links['type', kind], f'{label} ({count})')
        self.assertEqual(parsed.cards['block-photo']['data-review-status'], 'needs_review')
        self.assertEqual(parsed.links['review', 'all'], 'All (9)')
        self.assertEqual(parsed.links['review', 'pending'], 'Needing review (8)')
        self.assertEqual(parsed.links['review', 'approved'], 'Approved (1)')

    def test_filter_groups_empty_reset_and_dirty_dialog_are_labeled(self):
        self.document()
        parsed = FilterScreen(self.client.get('/structure').text)
        self.assertEqual(parsed.attrs['block-review-filter']['aria-label'], 'Review state')
        self.assertEqual(parsed.attrs['block-type-filter']['aria-label'], 'Block type')
        self.assertEqual(parsed.attrs['show-all-blocks']['aria-controls'], 'block-review-filter block-type-filter')
        self.assertEqual(parsed.attrs['block-filter-dialog']['aria-describedby'], 'block-filter-dialog-message')
        self.assertEqual(parsed.attrs['block-filter-notice']['role'], 'status')

    def test_classification_change_preserves_identity_provenance_and_undo_then_updates_group(self):
        document = self.document()
        original = copy.deepcopy(document['blocks'][1])
        current = update_block(self.root, 'paragraph', {'type': 'list', 'content': original['content'],
                    'expected_review_token': review_token(document)})
        block = current['blocks'][1]
        self.assertEqual(block['id'], original['id'])
        self.assertEqual(block['children'][0]['content'], original['content'])
        self.assertEqual(block['children'][0]['provenance'], {**original['provenance'],
             'review_changes': block['children'][0]['provenance']['review_changes']})
        self.assertEqual(block['review']['status'], 'needs_review')
        parsed = FilterScreen(self.client.get('/structure').text)
        self.assertEqual(parsed.cards['block-paragraph']['data-filter-type'], 'list')
        self.assertEqual(parsed.links['type', 'paragraph'], 'Paragraphs (0)')
        self.assertEqual(parsed.links['type', 'list'], 'Lists (2)')
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'][1], original)

    def test_stale_text_save_or_approval_preserves_new_decision_and_history(self):
        document = self.document()
        token = review_token(document)
        update_block(self.root, 'heading', {'review_status': 'approved'})
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in (self.root/'review').rglob('*.json')}
        for endpoint in ('/api/blocks/paragraph', '/api/blocks/paragraph/save-and-approve'):
            response = self.client.post(endpoint, headers=self.headers, json={
                'type': 'list', 'content': 'Attempted stale change', 'expected_review_token': token})
            self.assertEqual(response.status_code, 400)
            self.assertIn('project changed', response.json()['error'])
            self.assertEqual({str(p.relative_to(self.root)): p.read_bytes() for p in (self.root/'review').rglob('*.json')}, before)

    def test_read_only_filter_screen_has_save_snapshots_without_modifying_current_data(self):
        self.document()
        before = (self.root/'review/current.json').read_bytes()
        screen = self.client.get('/structure').text
        for identity in ('heading', 'paragraph', 'list', 'table'):
            card = screen.split('id="block-' + identity + '"')[1].split('</article>')[0]
            self.assertRegex(card, r'name="expected_review_token" value="[a-f0-9]+"')
        self.assertEqual((self.root/'review/current.json').read_bytes(), before)
