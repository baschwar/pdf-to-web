"""Saved block previews share exports without creating authoring state."""
import copy
import json
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from pdf_to_web.block_preview import saved_block_preview
from pdf_to_web.exporters import html, gutenberg, wxr
from pdf_to_web.exporters.common import render_inline
from pdf_to_web.review_state import ensure_review_document, original_path, review_path, undo_last
from pdf_to_web.web import _manual_reference_notice
from pdf_to_web.wordpress_preview import preview_available, render_gutenberg_preview
import test_web_app as web_tests


def footnote_document():
    return {'metadata': {'title': 'Not a fragment title'}, 'blocks': [
        {'id': 'p1', 'type': 'paragraph', 'content': 'Bold 1 and link after.',
         'runs': [{'type': 'strong', 'text': 'Bold 1 and '},
                  {'type': 'link', 'text': 'link', 'url': 'https://example.test/guide'},
                  {'type': 'text', 'text': ' after.'}],
         'footnote_references': [{'id': 'ref-1', 'footnote_id': 'fn-1', 'marker': '1', 'start': 5, 'end': 6}]},
        {'id': 'p2', 'type': 'paragraph', 'content': 'Other 1.',
         'footnote_references': [{'id': 'ref-2', 'footnote_id': 'fn-1', 'marker': '1', 'start': 6, 'end': 7}]}],
        'footnotes': [{'id': 'fn-1', 'marker': '1', 'text': 'Note body.',
                      'references': [{'id': 'ref-1', 'block_id': 'p1', 'marker': '1'},
                                     {'id': 'ref-2', 'block_id': 'p2', 'marker': '1'}]}]}


class Markup(HTMLParser):
    def __init__(self, value):
        super().__init__()
        self.tags = []
        self.feed(value)

    def handle_starttag(self, tag, attributes):
        self.tags.append((tag, dict(attributes)))


class BlockRenderingTests(unittest.TestCase):
    def test_saved_line_breaks_remain_native_across_html_gutenberg_wxr_and_preview(self):
        block = {'id': 'breaks', 'type': 'paragraph', 'content': 'First & <tag>\nSecond\n\nFourth'}
        document = {'blocks': [block]}
        before = copy.deepcopy(document)
        expected = '<p>First &amp; &lt;tag&gt;<br>Second<br><br>Fourth</p>'
        semantic = html.render_document(document)
        blocks = gutenberg.render_document(document)
        xml = wxr.render_wxr([{'slug': 'breaks', 'content': blocks}])
        encoded = ET.fromstring(xml).find('.//{http://purl.org/rss/1.0/modules/content/}encoded').text
        for output in (semantic, blocks, encoded, saved_block_preview(block, document)):
            self.assertIn(expected, output)
        self.assertIn('<!-- wp:paragraph -->', blocks)
        self.assertNotIn('<!-- wp:html', blocks)
        if preview_available():
            self.assertIn(expected.replace('<br>', '<br />'), render_gutenberg_preview(blocks).html)
        self.assertEqual(document, before)

    def test_breaks_preserve_styled_list_item_identity_and_raw_footnote_offsets(self):
        text = 'Intro\r\nClaim 1\n\nEnd'
        item = {'id': 'item', 'type': 'list_item', 'content': text,
                'runs': [{'type': 'strong', 'text': 'Intro\r\n'},
                         {'type': 'emphasis', 'text': 'Claim 1\n\nEnd'}],
                'footnote_references': [{'id': 'ref', 'footnote_id': 'note', 'marker': '1',
                                         'start': text.index('1'), 'end': text.index('1') + 1}]}
        block = {'id': 'list', 'type': 'list', 'children': [item]}
        before = copy.deepcopy(block)
        expected = '<strong>Intro<br></strong><em>Claim </em><sup><a href="#note" id="ref">1</a></sup><em><br><br>End</em>'
        document = {'blocks': [block]}
        self.assertIn(expected, html.render_block(block))
        blocks = gutenberg.render_document(document)
        self.assertIn(expected, blocks)
        self.assertIn('<!-- wp:list', blocks)
        self.assertNotIn('<!-- wp:html', blocks)
        self.assertEqual(block, before)

    def test_styled_reference_position_and_native_wrappers_match_html_gutenberg_wxr(self):
        document = footnote_document()
        before = copy.deepcopy(document)
        semantic = html.render_document(document)
        blocks = gutenberg.render_document(document)
        xml = wxr.render_wxr([{'title': 'Fixture', 'slug': 'fixture', 'content': blocks}])
        decoded = ET.fromstring(xml).find('.//{http://purl.org/rss/1.0/modules/content/}encoded').text
        expected = '<strong>Bold </strong><sup><a href="#fn-1" id="ref-1">1</a></sup><strong> and </strong>'
        for value in (semantic, blocks, decoded):
            self.assertIn(expected, value)
            self.assertEqual(value.count('id="ref-1"'), 1)
            self.assertIn('aria-label="Back to reference 1 for footnote 1"', value)
            self.assertIn('aria-label="Back to reference 2 for footnote 1"', value)
            self.assertIn('href="#ref-2"', value)
        self.assertEqual(decoded, blocks)
        self.assertEqual(blocks.count('<!-- wp:paragraph -->'), 2)
        self.assertEqual(blocks.count('<!-- wp:html -->'), 1)  # Existing endnotes only.
        self.assertEqual(document, before)

    def test_reference_crosses_runs_without_nested_links_or_duplicated_marker(self):
        block = {'content': 'É & 12 next', 'runs': [
            {'type': 'emphasis', 'text': 'É & 1'},
            {'type': 'link', 'text': '2 next', 'url': 'https://example.test'}],
            'footnote_references': [{'id': 'r12', 'footnote_id': 'n12', 'marker': '12', 'start': 4, 'end': 6}]}
        markup = render_inline(block)
        self.assertEqual(markup, '<em>É &amp; </em><sup><a href="#n12" id="r12">12</a></sup><a href="https://example.test"> next</a>')

    def test_multiple_legacy_markers_and_stale_offsets_use_text_not_html(self):
        block = {'content': 'One 1 & two 2.', 'runs': [{'type': 'strong', 'text': 'One 1 & two 2.'}],
                 'footnote_references': [{'id': 'r1', 'footnote_id': 'n1', 'marker': '1', 'start': 0, 'end': 1},
                                         {'id': 'r2', 'footnote_id': 'n2', 'marker': '2'}]}
        markup = render_inline(block)
        self.assertIn('One </strong><sup>', markup)
        self.assertIn('&amp; two </strong><sup>', markup)
        self.assertEqual(markup.count('<sup>'), 2)
        plain = {key: value for key, value in block.items() if key != 'runs'}
        self.assertEqual(render_inline(plain).count('<sup>'), 2)

    def test_explicit_legacy_run_reference_without_marker_is_retained(self):
        self.assertEqual(render_inline({'runs': [{'type': 'text', 'text': 'Claim'}],
            'footnote_references': [{'id': 'r', 'footnote_id': 'n', 'marker': '1'}]}),
            'Claim<sup><a href="#n" id="r">1</a></sup>')

    def test_fragment_has_relevant_notes_only_and_no_added_title_or_foreign_backlink(self):
        document = footnote_document()
        fragment = html.render_block(document['blocks'][0], document=document)
        self.assertNotIn('<h1', fragment)
        self.assertNotIn('Not a fragment title', fragment)
        self.assertIn('Note body.', fragment)
        self.assertIn('href="#ref-1"', fragment)
        self.assertNotIn('ref-2', fragment)
        ids = [attrs['id'] for _, attrs in Markup(fragment).tags if 'id' in attrs]
        self.assertEqual(len(ids), len(set(ids)))

    def test_nested_list_formats_and_omissions_match_export_without_model_change(self):
        block = {'id': 'list', 'type': 'list', 'ordered': True, 'start': 3, 'children': [
            {'id': 'item', 'type': 'list_item', 'content': 'Main', 'runs': [{'type': 'strong', 'text': 'Main'}],
             'children': [{'id': 'nested', 'type': 'list', 'ordered': True, 'marker_style': 'lower-alpha',
                           'children': [{'id': 'detail', 'type': 'list_item', 'content': 'Detail'},
                                        {'id': 'omit', 'type': 'list_item', 'content': 'Excluded', 'excluded': True}]}]}]}
        before = copy.deepcopy(block)
        fragment = html.render_block(block, document={})
        self.assertIn('<ol start="3"><li><strong>Main</strong><ol type="a">', fragment)
        self.assertNotIn('Excluded', fragment)
        blocks = gutenberg.render_document({'blocks': [block]})
        self.assertIn('<!-- wp:list ', blocks)
        self.assertNotIn('<!-- wp:html', blocks)
        self.assertEqual(block, before)

    def test_safe_preview_keeps_note_navigation_and_removes_unsafe_or_external_targets(self):
        document = footnote_document()
        block = document['blocks'][0]
        block['runs'].extend([{'type': 'link', 'text': 'unsafe', 'url': 'javascript:alert(1)'},
                              {'type': 'text', 'text': '<script>alert(1)</script>'}])
        before = copy.deepcopy(document)
        preview = saved_block_preview(block, document)
        self.assertIn('href="about:srcdoc#fn-1"', preview)
        self.assertIn('aria-label="Back to footnote reference 1"', preview)
        self.assertIn('title="Link destination: https://example.test/guide"', preview)
        self.assertNotIn('href="https:', preview)
        self.assertNotIn('javascript:', preview)
        self.assertNotIn('<script>', preview)
        self.assertIn('&lt;script&gt;', preview)
        self.assertIn("default-src 'none'", preview)
        self.assertEqual(document, before)

    def test_empty_excluded_legacy_list_and_plain_citations_are_clear_and_recoverable(self):
        self.assertIn('No saved text.', saved_block_preview({'type': 'paragraph', 'content': ''}, {}))
        self.assertIn('omitted from exports', saved_block_preview({'type': 'paragraph', 'content': 'Kept', 'excluded': True}, {}))
        self.assertIn('<li>Retained text</li>', saved_block_preview({'type': 'list', 'content': 'Retained text'}, {}))
        plain = saved_block_preview({'type': 'paragraph', 'content': 'Study 3'}, {})
        self.assertIn('<p>Study 3</p>', plain)
        self.assertNotIn('<sup>', plain)

    def test_reference_notice_requires_included_reference_section_not_ordinary_numbers(self):
        document = {'blocks': [{'type': 'paragraph', 'content': '2026 data 3'},
            {'type': 'heading', 'content': 'References'}, {'type': 'list', 'children': [
                {'type': 'list_item', 'content': 'First'}, {'type': 'list_item', 'content': 'Second'}]}]}
        before = copy.deepcopy(document)
        self.assertIn('References section detected.', _manual_reference_notice(document))
        self.assertEqual(document, before)
        document['blocks'][1]['excluded'] = True
        self.assertEqual(_manual_reference_notice(document), '')
        document['blocks'][1].pop('excluded')
        document['blocks'][2]['children'][1]['excluded'] = True
        self.assertEqual(_manual_reference_notice(document), '')

    @unittest.skipUnless(preview_available(), 'Existing optional WordPress preview unavailable')
    def test_wordpress_preview_preserves_existing_footnote_markup_and_labels(self):
        preview = render_gutenberg_preview(gutenberg.render_document(footnote_document()))
        self.assertIn('<sup><a href="#fn-1" id="ref-1">1</a></sup>', preview.html)
        self.assertIn('aria-label="Back to reference 1 for footnote 1"', preview.html)
        self.assertIn('aria-labelledby="footnotes-heading"', preview.html)
        self.assertIn('core/paragraph', preview.block_types)
        self.assertEqual(preview.block_types.count('core/html'), 1)


class BlockPreviewRoutesTests(unittest.TestCase):
    def setUp(self):
        self.fixture = web_tests.WebAppTests('test_startup_bootstrap_and_pages')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.project
        self.client = self.fixture.client
        self.fixture.bootstrap()

    def test_structure_has_one_editor_and_hidden_lazy_preview_without_project_writes(self):
        self.client.get('/structure')  # Existing initialization, outside preview switching.
        before = {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        response = self.client.get('/structure')
        parser = Markup(response.text)
        previews = [attrs for tag, attrs in parser.tags if tag == 'iframe' and 'data-saved-preview' in attrs]
        tabs = [attrs for _, attrs in parser.tags if attrs.get('role') == 'tab']
        self.assertEqual(len(previews), 2)
        self.assertEqual(len(tabs), 4)
        for frame in previews:
            self.assertNotIn('srcdoc', frame)
            self.assertEqual(frame['sandbox'], 'allow-same-origin')
            self.assertNotIn('<h1', frame['data-saved-preview'])
        for identity in ('p1', 'p2'):
            panel = next(attrs for _, attrs in parser.tags if attrs.get('id') == 'content-preview-' + identity)
            self.assertIn('hidden', panel)
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})

    def test_save_approval_stale_rejection_undo_and_reopen_feed_saved_preview(self):
        self.client.get('/structure')
        document = ensure_review_document(self.root)
        from pdf_to_web.image_review import review_token
        token = review_token(document)
        original = original_path(self.root).read_bytes()
        response = self.client.post('/api/blocks/p1', headers=self.fixture.headers(),
            json={'content': 'New saved text\n\nSecond part', 'expected_review_token': token})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['block_status'], 'needs_review')
        page = self.client.get('/structure').text
        preview = next(attrs['data-saved-preview'] for tag, attrs in Markup(page).tags
                       if tag == 'iframe' and attrs.get('title') == 'Formatted preview for block 2')
        self.assertIn('<p>New saved text<br><br>Second part</p>', preview)
        saved = review_path(self.root).read_bytes()
        rejected = self.client.post('/api/blocks/p1', headers=self.fixture.headers(),
            json={'content': 'Stale text', 'expected_review_token': token})
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(review_path(self.root).read_bytes(), saved)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['content'], 'Original one')
        approved = self.client.post('/api/blocks/p1/save-and-approve', headers=self.fixture.headers(),
            json={'content': 'Approved text\n\nSecond part', 'expected_review_token': review_token(ensure_review_document(self.root))})
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()['block_status'], 'approved')
        self.assertIn('Approved text', self.client.get('/structure').text)
        self.assertEqual(original_path(self.root).read_bytes(), original)
