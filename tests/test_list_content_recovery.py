"""Recover malformed lists explicitly without hiding or silently approving text."""
import copy
import re
import unittest
import xml.etree.ElementTree as ET

import test_image_draft_routes as routes
from pdf_to_web.exporters import html, gutenberg, markdown, wxr
from pdf_to_web.export import export_project
from pdf_to_web.output_page_export import export_pages
from pdf_to_web.errors import PdfToWebError
from pdf_to_web.exporters.common import list_render_items
from pdf_to_web.publication import effective_block_status, readiness_findings
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, undo_last
from pdf_to_web.web import _source_regions, _source_region_coverage


class ListContentRecoveryTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def document(self, block):
        document = ensure_review_document(self.root)
        document['blocks'] = [block]
        document['review']['complex_visuals'] = []
        document['review']['issues'] = []
        document.pop('output_pages', None)
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def malformed(self):
        return {'id': 'retained', 'type': 'list', 'content': 'Read the guide carefully.',
                'children': [], 'provenance': {'source_page': 1, 'bounding_box': [10, 20, 300, 40]},
                'runs': [{'type': 'strong', 'text': 'Read '},
                         {'type': 'link', 'text': 'the guide', 'url': 'https://example.test/guide'},
                         {'type': 'text', 'text': ' carefully.'}], 'review': {'status': 'approved'}}

    def test_legacy_text_visible_in_editor_and_all_serializers_without_mutation(self):
        document = self.document(self.malformed())
        before = (self.root / 'review/current.json').read_bytes()
        screen = self.client.get('/structure').text
        self.assertIn('Read the guide carefully.</textarea>', screen)
        self.assertIn('stored list text has no list items', screen)
        self.assertEqual(effective_block_status(document['blocks'][0]), 'needs_review')
        self.assertIn('list_items_missing', [i['code'] for i in readiness_findings(document)])
        semantic = html.render_document(document)
        blocks = gutenberg.render_document(document)
        for markup in (semantic, blocks):
            self.assertIn('<strong>Read </strong>', markup)
            self.assertIn('href="https://example.test/guide"', markup)
            self.assertIn('carefully.', markup)
            self.assertIn('<li>', markup)
        self.assertIn('Read the guide carefully.', markdown.render_document(document))
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertEqual(document, ensure_review_document(self.root))

    def test_blank_save_and_direct_approval_reject_without_changes(self):
        self.document(self.malformed())
        before = (self.root / 'review/current.json').read_bytes()
        for changes in ({'content': ''}, {'type': 'paragraph', 'content': ' '}, {'review_status': 'approved'}):
            with self.subTest(changes=changes):
                result = self.client.post('/api/blocks/retained', headers=self.headers, json=changes)
                self.assertEqual(result.status_code, 400)
                self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_malformed_list_blocks_publication_before_writing_any_format(self):
        self.document(self.malformed())
        for target in ('html', 'markdown', 'gutenberg', 'wordpress-xml', 'all'):
            with self.subTest(target=target), self.assertRaisesRegex(PdfToWebError, 'stored list text'):
                export_project(self.root, target)
        with self.assertRaisesRegex(PdfToWebError, 'stored list text'):
            export_pages(self.root)
        self.assertFalse(list((self.root / 'output/html').glob('*.html')))

    def test_recovered_then_reviewed_actual_exports_retain_rich_content_in_wxr(self):
        self.document(self.malformed())
        update_block(self.root, 'retained', {'content': 'Read the guide carefully.'})
        update_block(self.root, 'retained', {'review_status': 'approved'})
        paths = export_project(self.root, 'all')
        xml_paths = [p for p in paths if p.suffix == '.xml']
        self.assertTrue(xml_paths)
        content = ET.parse(xml_paths[0]).find('.//{' + wxr.CONTENT_NS + '}encoded').text
        self.assertIn('<li>', content)
        self.assertIn('<strong>Read </strong>', content)
        self.assertIn('href="https://example.test/guide"', content)
        self.assertIn('carefully.', content)

    def test_explicit_recovery_preserves_rich_content_provenance_and_undo(self):
        before = self.document(self.malformed())
        current = update_block(self.root, 'retained', {'content': 'Read the guide carefully.', 'review_status': 'approved'})
        block = current['blocks'][0]
        self.assertEqual(block['id'], 'retained')
        self.assertEqual(len(block['children']), 1)
        child = block['children'][0]
        self.assertEqual(child['runs'], before['blocks'][0]['runs'])
        self.assertEqual(child['provenance']['bounding_box'], [10, 20, 300, 40])
        self.assertEqual(child['provenance']['source_page'], 1)
        self.assertEqual(block['review']['status'], 'needs_review')
        self.assertEqual(child['review']['status'], 'needs_review')
        self.assertNotIn('runs', block)
        self.assertEqual(ensure_review_document(self.root)['blocks'], current['blocks'])
        update_block(self.root, 'retained', {'review_status': 'approved'})
        self.assertEqual(effective_block_status(ensure_review_document(self.root)['blocks'][0]), 'approved')
        undo_last(self.root)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])

    def test_unchanged_type_only_conversion_builds_one_item_preserving_line_breaks(self):
        source = self.malformed()
        source.update(type='paragraph', content='First line\ncontinuation', runs=[{'type': 'emphasis', 'text': 'First line\ncontinuation'}])
        before = self.document(source)
        current = update_block(self.root, 'retained', {'type': 'list'})
        self.assertEqual(len(current['blocks'][0]['children']), 1)
        self.assertEqual(current['blocks'][0]['children'][0]['content'], source['content'])
        self.assertEqual(current['blocks'][0]['children'][0]['runs'], source['runs'])
        self.assertEqual(current['blocks'][0]['review']['status'], 'needs_review')
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])

    def test_blank_conversion_rejects_without_losing_existing_paragraph(self):
        source = self.malformed()
        source['type'] = 'paragraph'
        self.document(source)
        before = (self.root / 'review/current.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'blank save'):
            update_block(self.root, 'retained', {'type': 'list', 'content': ''})
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_retained_runs_without_content_are_displayed_and_recovered_without_losing_formatting(self):
        block = self.malformed()
        block['content'] = ''
        before = self.document(block)
        self.assertIn('Read the guide carefully.</textarea>', self.client.get('/structure').text)
        current = update_block(self.root, 'retained', {'content': 'Read the guide carefully.'})
        self.assertEqual(current['blocks'][0]['children'][0]['runs'], block['runs'])
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])

    def test_reopen_does_not_strip_explicit_text_or_shift_footnotes_with_literal_marker(self):
        block = {'id': 'text', 'type': 'list', 'ordered': True, 'content': '1. Read1', 'children': [],
                 'footnote_references': [{'id': 'ref1', 'footnote_id': 'note1', 'marker': '1', 'start': 7, 'end': 8}]}
        self.document(block)
        current = update_block(self.root, 'text', {'content': '1. Read1'})
        reopened = ensure_review_document(self.root)
        child = reopened['blocks'][0]['children'][0]
        self.assertEqual(child['content'], '1. Read1')
        self.assertEqual(child['footnote_references'], block['footnote_references'])
        self.assertEqual(reopened['blocks'], current['blocks'])
        self.assertIn('id="ref1"', html.render_document(reopened))

    def test_footnote_recovery_preserves_offsets_backlinks_and_undo(self):
        block = {'id': 'text', 'type': 'list', 'content': 'Read1', 'children': [],
                 'footnote_references': [{'id': 'ref1', 'footnote_id': 'note1', 'marker': '1', 'start': 4, 'end': 5}]}
        document = self.document(block)
        document['footnotes'] = [{'id': 'note1', 'marker': '1', 'text': 'Note', 'references': [{'id': 'ref1', 'block_id': 'text'}]}]
        save_review_document(self.root, document)
        before = ensure_review_document(self.root)
        with self.assertRaisesRegex(ValueError, 'footnote'):
            update_block(self.root, 'text', {'content': 'Changed1'})
        current = update_block(self.root, 'text', {'content': 'Read1'})
        child = current['blocks'][0]['children'][0]
        self.assertEqual(child['footnote_references'], block['footnote_references'])
        self.assertEqual(current['footnotes'][0]['references'][0]['block_id'], child['id'])
        self.assertNotIn('footnote_references', current['blocks'][0])
        markup = html.render_document(current)
        self.assertEqual(markup.count('id="ref1"'), 1)
        self.assertIn('href="#ref1"', markup)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['footnotes'], before['footnotes'])

    def test_nested_malformed_list_blocks_owner_approval_and_export_readiness(self):
        inner = self.malformed()
        owner = {'id': 'owner', 'type': 'list', 'children': [{'id': 'item', 'type': 'list_item', 'content': 'Step', 'children': [inner]}], 'review': {'status': 'approved'}}
        document = self.document(owner)
        self.assertEqual(effective_block_status(document['blocks'][0]), 'needs_review')
        with self.assertRaisesRegex(ValueError, 'stored list text'):
            update_block(self.root, 'owner', {'review_status': 'approved'})
        self.assertIn('Read the guide carefully.', re.sub('<[^>]+>', '', html.render_document(document)))

    def test_existing_valid_list_and_exclusions_are_unchanged(self):
        valid = {'type': 'list', 'content': 'Old summary', 'children': [{'id': 'item', 'type': 'list_item', 'content': 'Actual item'}]}
        self.assertEqual(list_render_items(valid), valid['children'])
        excluded = self.malformed()
        excluded['review']['status'] = 'excluded'
        self.assertEqual(html._block(excluded), '')
        self.assertEqual(gutenberg.render_block(excluded), '')


class SourceRegionCoverageTests(unittest.TestCase):
    def test_nested_paragraph_includes_recorded_box_once_and_reports_only_missing_regions(self):
        box = [10, 20, 300, 40]
        root = {'type': 'list', 'provenance': {'source_page': 8}, 'children': [
            {'type': 'list_item', 'provenance': {'source_page': 8, 'bounding_box': [10, 50, 300, 60]}, 'children': [
                {'type': 'paragraph', 'content': 'Nested note', 'provenance': {'source_page': 8, 'bounding_box': box}},
                {'type': 'paragraph', 'content': 'Same recorded region', 'provenance': {'source_page': 8, 'bounding_box': box}},
                {'type': 'paragraph', 'content': 'No region', 'provenance': {'source_page': 8}},
                {'type': 'paragraph', 'content': 'Other page', 'provenance': {'source_page': 9, 'bounding_box': [1, 2, 3, 4]}},
                {'type': 'paragraph', 'content': 'Excluded', 'review': {'status': 'excluded'}, 'provenance': {'source_page': 8}},
                {'type': 'paragraph', 'content': 'Invalid', 'provenance': {'source_page': 8, 'bounding_box': [1, 2, float('nan'), 4]}}
            ]}]}
        before = copy.deepcopy(root)
        self.assertEqual(_source_regions(root), [[10, 50, 300, 60], box])
        self.assertIn('2 nested text', _source_region_coverage(root))
        self.assertEqual(root['children'][0]['children'][0], before['children'][0]['children'][0])

    def test_missing_child_boxes_keep_only_recorded_container_region_with_partial_notice(self):
        root = {'type': 'list', 'provenance': {'source_page': 8, 'bounding_box': [1, 2, 3, 4]},
                'children': [{'type': 'list_item', 'content': 'Step', 'provenance': {'source_page': 8}}]}
        self.assertEqual(_source_regions(root), [[1, 2, 3, 4]])
        self.assertIn('Unoutlined text may still be present', _source_region_coverage(root))
