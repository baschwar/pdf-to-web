from review_helpers import stamp_fixture_approvals, approve_publication_fixture
import copy
import json
import re
import unittest

import test_image_draft_routes as routes
from pdf_to_web.accessibility import assess_document
from pdf_to_web.exporters import html, gutenberg, wxr
from pdf_to_web.normalize import _apply_link_annotations
from pdf_to_web.review_state import ensure_review_document, original_path, save_review_document, update_block, undo_last, restore_source_links, move_block


class AccessibilityWorkflowFollowupTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def ready(self):
        document = ensure_review_document(self.root)
        for block in document['blocks']:
            block.setdefault('review', {})['status'] = 'approved'
            if block.get('type') == 'image':
                block['alt'] = block.get('alt') or 'Synthetic alternative'
                block['wordpress_url'] = 'https://example.test/upload.png'
        document['review']['complex_visuals'][0]['accessibility']['short_alt'] = 'Synthetic chart'
        document['review']['complex_visuals'][0]['status'] = 'reviewed'
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        return document

    def linked_list(self):
        document = self.ready()
        url = 'https://example.test/resources'
        child = {'id': 'resource', 'type': 'list_item', 'content': 'Resources: (' + url + ')',
                 'runs': [{'type': 'strong', 'text': 'Resources: '}, {'type': 'text', 'text': '('},
                          {'type': 'link', 'text': url, 'url': url}, {'type': 'text', 'text': ')'}],
                 'source_links': [{'url': url, 'inline_preserved': True}], 'children': [],
                 'provenance': {'source_page': 1}, 'review': {'status': 'approved'}}
        document['blocks'][1] = {'id': 'p', 'type': 'list', 'content': child['content'], 'children': [child],
                                  'provenance': {'source_page': 1}, 'review': {'status': 'approved'}}
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        return document, url

    def test_accessibility_block_buttons_have_explicit_return_context(self):
        self.linked_list()
        page = self.client.get('/accessibility').text
        self.assertIn('href="/structure?return_to=accessibility&amp;finding=link%3Aresource%3A3#block-p" role="button" class="secondary compact-action">Open block', page)
        self.assertIn('id="finding-link:resource:3" tabindex="-1"', page)

    def test_finding_numbers_match_current_reading_order_including_nested_links(self):
        self.linked_list()
        update_block(self.root, 'p', {'review_status': 'needs_review'})
        def location(finding):
            page = self.client.get('/accessibility').text
            return re.search(r'<article id="finding-' + re.escape(finding) + r'".*?</article>', page, re.S).group(0)
        self.assertIn('Source page 1 · Block 2', location('structure:p'))
        self.assertIn('Source page 1 · Block 2', location('link:resource:3'))
        first = ensure_review_document(self.root)['blocks'][0]['id']
        update_block(self.root, first, {'review_status': 'excluded'})
        self.assertIn('Source page 1 · Block 2', location('structure:p'))
        move_block(self.root, 'p', 'up')
        self.assertIn('Source page 1 · Block 1', location('structure:p'))
        self.assertIn('Source page 1 · Block 1', location('link:resource:3'))
        undo_last(self.root)
        self.assertIn('Source page 1 · Block 2', location('structure:p'))

    def test_resolved_diagnostic_is_history_with_no_action_and_saved_decision_retained(self):
        document = self.ready()
        document['review']['issues'] = [{'code': 'block_review_required', 'message': 'Old extraction note', 'block_ids': ['photo']}]
        document['accessibility_review'] = {'decisions': {'diagnostic:block_review_required:document': {'status': 'approved', 'note': 'Reviewed in source'}}}
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        before = copy.deepcopy(ensure_review_document(self.root))
        page = self.client.get('/accessibility').text
        self.assertIn('<details class="diagnostic-history">', page)
        self.assertIn('No action is needed.', page)
        self.assertNotIn('<h2 id="accessibility-diagnostics">', page)
        self.assertEqual(ensure_review_document(self.root), before)

    def test_accessibility_continue_waits_for_scan_and_pending_document_stays_blocked(self):
        self.ready()
        page = self.client.get('/accessibility').text
        self.assertRegex(page, r'id="accessibility-complete"[^>]*data-document-ready="true" hidden')
        self.assertIn('Continue to Arrange Pages', page)
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        self.assertIn('data-document-ready="false" hidden', self.client.get('/accessibility').text)

    def test_preview_has_two_export_handoffs_and_arrangement_undo_is_neutral(self):
        self.assertEqual(self.client.get('/preview').text.count('>Continue to Export</a>'), 2)
        self.assertIn('id="output-page-undo" class="neutral-action"', self.client.get('/output-pages').text)

    def test_export_hides_passing_checks_but_retains_actual_problems(self):
        self.ready()
        page = self.client.get('/export').text
        self.assertNotIn('id="readiness-heading"', page)
        self.assertNotIn('0 unresolved diagnostic', page)
        self.assertNotIn('0 images still need', page)
        self.assertIn('id="copy-page-title-status" role="status"', page)
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        page = self.client.get('/export').text
        self.assertIn('Pending 1 review task', page)
        self.assertIn('1 block review', page)
        self.assertNotIn('<li>0 ', page)

    def test_export_names_only_unmapped_meaningful_images(self):
        document = self.ready()
        document['blocks'][2].pop('wordpress_url')
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        page = self.client.get('/export').text
        missing = re.search(r'<div id="unmapped-media">(.*?)</div>', page, re.S).group(1)
        self.assertIn('#block-photo', missing)
        self.assertNotIn('#block-decoration', missing)
        self.assertNotIn('#block-ambiguous', missing)
        self.assertIn('importing the content WXR is optional', page)

    def test_arranged_semantic_preview_uses_local_assets_even_when_wordpress_mapped(self):
        document = self.ready()
        before = copy.deepcopy(ensure_review_document(self.root))
        slug = document['output_pages']['pages'][0]['slug']
        preview = self.client.get('/output-preview/' + slug + '.html')
        self.assertEqual(preview.status_code, 200)
        self.assertIn('src="/api/preview/images/photo.png"', preview.text)
        self.assertNotIn('src="images/photo.png"', preview.text)
        self.assertEqual(self.client.get('/api/preview/images/photo.png').content, b'fixture image bytes')
        contents = self.client.get('/output-pages-contents')
        self.assertIn('href="/output-preview/' + slug + '.html"', contents.text)
        self.assertEqual(ensure_review_document(self.root), before)

    def test_unchanged_list_save_keeps_runs_review_and_source_provenance(self):
        document, _ = self.linked_list()
        before = copy.deepcopy(document['blocks'][1]['children'])
        update_block(self.root, 'p', {'content': document['blocks'][1]['content'], 'review_status': 'approved'})
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['children'], before)

    def test_list_text_edit_keeps_destinations_labels_formatting_exports_and_undo(self):
        document, url = self.linked_list()
        original = copy.deepcopy(ensure_review_document(self.root))
        content = document['blocks'][1]['content'].replace(url, 'Visit the resource library')
        update_block(self.root, 'p', {'content': content, 'review_status': 'needs_review'})
        current = ensure_review_document(self.root)
        child = current['blocks'][1]['children'][0]
        self.assertEqual(child['id'], 'resource')
        self.assertEqual(child['source_links'], original['blocks'][1]['children'][0]['source_links'])
        self.assertEqual(''.join(r['text'] for r in child['runs']), content)
        self.assertEqual([r['url'] for r in child['runs'] if r['type'] == 'link'], [url])
        for markup in (html.render_document(current), gutenberg.render_document(current)):
            self.assertIn(f'<a href="{url}">Visit the resource library</a>', markup)
            self.assertIn('<strong>Resources: </strong>', markup)
        self.assertNotIn('URL used as link text', self.client.get('/accessibility').text)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], original['blocks'])

    def test_nested_link_label_save_updates_parent_editor_so_next_save_cannot_revert_it(self):
        _, url = self.linked_list()
        update_block(self.root, 'resource', {'link_index': 2, 'link_text': 'Resource library'})
        document = ensure_review_document(self.root)
        self.assertIn('Resource library', document['blocks'][1]['content'])
        update_block(self.root, 'p', {'content': document['blocks'][1]['content'], 'review_status': 'approved'})
        child = ensure_review_document(self.root)['blocks'][1]['children'][0]
        self.assertIn({'type': 'link', 'text': 'Resource library', 'url': url}, child['runs'])

    def test_editing_an_excluded_list_item_keeps_it_excluded_and_recoverable(self):
        document, url = self.linked_list()
        child = document['blocks'][1]['children'][0]
        child['review']['status'] = 'excluded'
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        update_block(self.root, 'p', {'content': document['blocks'][1]['content'].replace(url, 'Resource library')})
        current = ensure_review_document(self.root)
        self.assertEqual(current['blocks'][1]['children'][0]['review']['status'], 'excluded')
        self.assertEqual(current['blocks'][1]['children'][0]['runs'][2]['url'], url)
        self.assertNotIn('Resource library', html.render_document(current))

    def test_source_link_recovery_failure_does_not_save_partial_changes(self):
        document, url = self.linked_list()
        source = original_path(self.root)
        source.write_text(json.dumps(document))
        document['blocks'][1]['children'][0].pop('runs')
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        before = (self.root / 'review/current.json').read_bytes()
        with self.assertRaises(KeyError):
            restore_source_links(self.root, ['resource', 'missing-block'])
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_explicit_recovery_keeps_edited_labels_immutable_source_and_undo(self):
        document, url = self.linked_list()
        source = original_path(self.root)
        source.write_text(json.dumps(document))
        immutable = source.read_bytes()
        child = document['blocks'][1]['children'][0]
        child['content'] = child['content'].replace(url, 'Resource library')
        child.pop('runs')
        document['blocks'][1]['content'] = child['content']
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        before = copy.deepcopy(ensure_review_document(self.root))
        restored = restore_source_links(self.root, ['resource'])
        self.assertIn(f'<a href="{url}">Resource library</a>', gutenberg.render_document(restored))
        self.assertEqual(restored['blocks'][1]['review']['status'], 'needs_review')
        self.assertEqual(source.read_bytes(), immutable)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])

    def test_hyphen_damaged_visible_url_uses_pdf_destination_on_leaf_without_changing_text(self):
        url = 'https://example.test/I-Am-A-Student-and-I-Need'
        text = 'Student help: (https://example.test/I-Am-A-Studentand-I-Need)'
        child = {'id': 'li', 'type': 'list_item', 'content': text, 'provenance': {'source_page': 1, 'bounding_box': [20, 100, 300, 140]}}
        document = {'blocks': [{'id': 'list', 'type': 'list', 'content': text, 'children': [child], 'provenance': child['provenance']}]}
        _apply_link_annotations(document, [{'url': url, 'source_page': 1, 'bounding_box': [30, 110, 100, 130]}])
        self.assertEqual(document['source_links'][0]['source_block'], 'li')
        self.assertEqual(child['content'], text)
        self.assertEqual(child['runs'][1]['url'], url)
        self.assertIn(f'<a href="{url}">https://example.test/I-Am-A-Studentand-I-Need</a>', html.render_document(document))
