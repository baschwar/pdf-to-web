from review_helpers import stamp_fixture_approvals, approve_publication_fixture
import copy
import re
import unittest

import test_image_draft_routes as routes
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, undo_last


class DocumentStructureLayoutTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def test_export_rows_retain_file_forms_and_distinct_copy_submit_actions(self):
        page = self.client.get('/export').text
        for form_id, name, action in (
            ('media-wxr-form', 'media_wxr', 'Match WordPress media'),
            ('media-mapping-form', 'mapping', 'Import media mapping'),
        ):
            form = re.search(r'<form id="' + form_id + r'"[^>]*>.*?</form>', page, re.S).group()
            self.assertIn('class="inline-file-form"', form)
            self.assertIn('type="file" name="' + name + '"', form)
            self.assertIn('required', form)
            self.assertIn('type="submit" class="review-approve">' + action, form)
        form = re.search(r'<form id="export-form"[^>]*>.*?</form>', page, re.S).group()
        row = form[form.index('<div class="button-row workflow-next">'):]
        self.assertIn('type="button" id="copy-page-title"', row)
        self.assertIn('type="submit" class="review-approve" aria-describedby="export-availability"', row)
        self.assertIn('id="copy-page-title-status" role="status" aria-live="polite"', row)
        self.assertEqual(page.count('id="copy-page-title"'), 1)
        media = re.search(r'<form id="media-export-form"[^>]*>.*?</form>', page, re.S).group()
        actions = media[media.index('<div class="button-row">'):]
        self.assertIn('Prepare images ZIP and mapping CSV', actions)
        self.assertIn('type="button" class="neutral-action" id="media-export-undo"', actions)

    def test_mapping_preserves_content_review_and_undo_restores_unmapped_state(self):
        approve_publication_fixture(self.root)
        before = copy.deepcopy(ensure_review_document(self.root))
        response = self.client.post('/api/media-mapping', headers=self.headers, json={
            'csv': 'block_id,wordpress_url,wordpress_attachment_id,alt_text,caption\nphoto,https://example.test/photo.png,42,stale alt,stale caption\n'})
        self.assertEqual(response.status_code, 200, response.text)
        state = response.json()['export_state']
        self.assertTrue(state['publication_ready'])
        self.assertIn('Blocks reviewed 5', state['html'])
        self.assertIn('Pending 0 review tasks', state['html'])
        self.assertNotIn('href="/structure#block-photo"', state['html'])
        self.assertNotIn('changed after approval', state['html'])
        self.assertIn('Ready to export', state['announcement'])
        current = ensure_review_document(self.root)
        photo = next(b for b in current['blocks'] if b['id'] == 'photo')
        old = next(b for b in before['blocks'] if b['id'] == 'photo')
        self.assertEqual(photo['alt'], old['alt'])
        self.assertEqual(photo['caption'], old['caption'])
        self.assertEqual(current['review']['complex_visuals'], before['review']['complex_visuals'])
        rejected = self.client.post('/api/export', headers=self.headers, json={'target': 'html'})
        self.assertEqual(rejected.status_code, 200)
        undone = self.client.post('/api/media-export/undo', headers=self.headers, json={})
        self.assertEqual(undone.status_code, 200, undone.text)
        state = undone.json()['export_state']
        self.assertTrue(state['publication_ready'])
        self.assertIn('Blocks reviewed 5', state['html'])
        self.assertIn('Pending 0 review tasks', state['html'])
        self.assertNotIn('href="/structure#block-photo"', state['html'])
        self.assertIn('block-photo', state['unmapped_html'])
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])

    def test_identical_mapping_retains_approval_and_reports_ready(self):
        approve_publication_fixture(self.root)
        payload = {'csv': 'block_id,wordpress_url,wordpress_attachment_id\nphoto,https://example.test/photo.png,42\n'}
        self.client.post('/api/media-mapping', headers=self.headers, json=payload)
        approve_publication_fixture(self.root)
        before = copy.deepcopy(ensure_review_document(self.root)['blocks'])
        response = self.client.post('/api/media-mapping', headers=self.headers, json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['export_state']['publication_ready'])
        self.assertIn('Pending 0 review tasks', response.json()['export_state']['html'])
        self.assertEqual(ensure_review_document(self.root)['blocks'], before)

    def test_failed_mapping_does_not_change_saved_state_or_offer_new_readiness(self):
        from pdf_to_web.review_state import review_path
        approve_publication_fixture(self.root)
        before = review_path(self.root).read_bytes()
        for endpoint, payload in (
            ('/api/media-mapping', {'csv': 'block_id,wordpress_url\nphoto,https://example.test/photo.png\nunknown,https://example.test/unknown.png\n'}),
            ('/api/media-mapping-wxr', {'xml': '<broken'}),
        ):
            response = self.client.post(endpoint, headers=self.headers, json=payload)
            self.assertEqual(response.status_code, 400, response.text)
            self.assertNotIn('export_state', response.json())
            self.assertEqual(review_path(self.root).read_bytes(), before)

    def test_xml_matching_returns_same_authoritative_readiness_as_export_page(self):
        import csv
        approve_publication_fixture(self.root)
        prepared = self.client.post('/api/media-export', headers=self.headers, json={'image_prefix': 'qa-'})
        self.assertEqual(prepared.status_code, 200, prepared.text)
        with (self.root / 'output/wordpress/reports/media-mapping.csv').open() as stream:
            row = next(row for row in csv.DictReader(stream) if row['block_id'] == 'photo')
        xml = '<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel><item><wp:post_id>42</wp:post_id><wp:post_type>attachment</wp:post_type><wp:attachment_url>https://example.test/' + row['asset_filename'] + '</wp:attachment_url></item></channel></rss>'
        response = self.client.post('/api/media-mapping-wxr', headers=self.headers, json={'xml': xml})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['matched'], 1)
        state = response.json()['export_state']
        self.assertTrue(state['publication_ready'])
        self.assertIn('Pending 0 review tasks', state['html'])
        page = self.client.get('/export').text
        self.assertIn('<div id="export-review-state">' + state['html'] + '</div>', page)
        self.assertIn('data-publication-ready="true"', page)

    def test_filter_recovery_is_in_sticky_navigation_without_global_completion_claim(self):
        page = self.client.get('/structure').text
        from html.parser import HTMLParser
        class ToolbarParser(HTMLParser):
            def __init__(self):
                super().__init__(); self.stack = []; self.parents = {}; self.attrs = {}
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if values.get('id'):
                    self.parents[values['id']] = list(self.stack)
                    self.attrs[values['id']] = values
                if tag not in {'input', 'img', 'br', 'hr', 'meta', 'link'}:
                    self.stack.append(values.get('class', ''))
            def handle_endtag(self, tag):
                if self.stack: self.stack.pop()
        parsed = ToolbarParser(); parsed.feed(page)
        for target in ('block-filter-empty', 'show-all-blocks', 'previous-block', 'next-block'):
            self.assertIn('reading-order-header', parsed.parents[target])
        self.assertIn('hidden', parsed.attrs['block-filter-empty'])
        self.assertEqual(parsed.attrs['block-filter-empty-message']['role'], 'status')
        self.assertEqual(parsed.attrs['block-filter-empty-message']['aria-live'], 'polite')
        self.assertEqual(parsed.attrs['show-all-blocks']['aria-controls'], 'block-review-filter')
        self.assertEqual(page.count('id="block-filter-empty"'), 1)
        self.assertIn('>Show all blocks</a>', page)

    def resolved_document(self):
        document = ensure_review_document(self.root)
        for block in document['blocks']:
            block['alt'] = block.get('alt') or 'Synthetic alternative'
            block.setdefault('review', {})['status'] = 'approved'
        document['review']['complex_visuals'][0]['accessibility']['short_alt'] = 'Synthetic chart'
        document['review']['complex_visuals'][0]['status'] = 'reviewed'
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        return document

    def test_document_completion_handoff_preserves_accessibility_findings_and_state(self):
        document = self.resolved_document()
        # Block decisions are complete, but unrelated Accessibility checks remain.
        document['metadata']['language'] = ''
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        before = copy.deepcopy(ensure_review_document(self.root))
        page = self.client.get('/document').text
        self.assertIn('id="structure-review-complete"', page)
        self.assertIn('Continue to Accessibility', page)
        self.assertNotIn('0 unresolved diagnostic issues.', page)
        self.assertNotIn('<dd>Review Ready</dd>', page)
        self.assertEqual(ensure_review_document(self.root), before)

    def test_progress_and_action_precede_metadata_with_one_count_summary(self):
        self.resolved_document()
        page = self.client.get('/document').text
        self.assertLess(page.index('id="review-progress"'), page.index('<dl class="metadata-grid">'))
        self.assertLess(page.index('>Review structure</a>'), page.index('<dl class="metadata-grid">'))
        self.assertEqual(page.count('Blocks reviewed 5 · Excluded 0 · Total 5 blocks'), 1)
        self.assertEqual(page.count('Pending 0 review tasks'), 1)
        self.assertEqual(page.count('<progress '), 1)
        self.assertNotIn('<p>Approved 5', page)

    def test_pending_decision_changes_progress_and_undo_restores_document_handoff(self):
        self.resolved_document()
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        page = self.client.get('/document').text
        self.assertNotIn('id="structure-review-complete"', page)
        self.assertIn('Blocks reviewed 4', page)
        self.assertIn('Pending 1 review task', page)
        self.assertIn('value="4" max="5"', page)
        undo_last(self.root)
        self.assertIn('Continue to Accessibility', self.client.get('/document').text)

    def test_incomplete_description_empty_and_blocked_documents_cannot_continue(self):
        document = self.resolved_document()
        document['review']['complex_visuals'][0]['accessibility']['long_description'] = ''
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        page = self.client.get('/document').text
        self.assertNotIn('Continue to Accessibility', page)
        self.assertIn('1 description review', page)
        self.assertIn('href="/structure#visual-chart"', page)
        document['review']['status'] = 'conversion_blocked'
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        self.assertNotIn('Continue to Accessibility', self.client.get('/document').text)
        document['review']['status'] = 'review_ready'
        document['blocks'] = []
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        self.assertNotIn('Continue to Accessibility', self.client.get('/document').text)

    def test_unresolved_extraction_diagnostics_remain_visible(self):
        document = ensure_review_document(self.root)
        document['review']['issues'] = [{'code': 'extraction_warning', 'message': 'Synthetic source text requires inspection.'}]
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        page = self.client.get('/document').text
        self.assertIn('Synthetic source text requires inspection.', page)
        self.assertIn('1 unresolved diagnostic issue.', page)

    def test_history_uses_persisted_snapshots_and_disables_empty_undo(self):
        page = self.client.get('/structure').text
        self.assertIn('id="undo-action" type="button" class="secondary" disabled', page)
        self.assertIn('<details class="review-history">', page)
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        # A new page request sees history from the saved project.
        page = self.client.get('/structure').text
        self.assertNotIn('id="undo-action" type="button" class="secondary" disabled', page)
        self.assertIn('including changes from earlier sessions', page)
        undo_last(self.root)
        self.assertIn('id="undo-action" type="button" class="secondary" disabled', self.client.get('/structure').text)

    def test_reading_order_undo_tracks_saved_edits_and_restores_block_state(self):
        before = ensure_review_document(self.root)
        page = self.client.get('/structure').text
        undo = re.search(r'<button id="reading-order-undo"[^>]*>', page).group()
        self.assertIn(' disabled', undo)
        self.assertGreater(page.index(undo), page.index('<h2 id="blocks-heading">Reading order</h2>'))
        self.assertLess(page.index(undo), page.index('id="previous-block"'))
        edit = self.client.post('/api/blocks/photo', headers=self.headers,
                                json={'alt': 'Edited synthetic alternative', 'review_status': 'needs_review'})
        self.assertEqual(edit.status_code, 200, edit.text)
        undo = re.search(r'<button id="reading-order-undo"[^>]*>', self.client.get('/structure').text).group()
        self.assertNotIn(' disabled', undo)
        response = self.client.post('/api/review/undo', headers=self.headers, json={})
        self.assertEqual(response.status_code, 200, response.text)
        restored = ensure_review_document(self.root)
        for field in ('blocks', 'output_pages', 'accessibility_review'):
            self.assertEqual(restored.get(field), before.get(field))
        undo = re.search(r'<button id="reading-order-undo"[^>]*>', self.client.get('/structure').text).group()
        self.assertIn(' disabled', undo)

    def test_reading_order_undo_is_absent_when_conversion_blocks_editing(self):
        document = ensure_review_document(self.root)
        document['review']['status'] = 'conversion_blocked'
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        self.assertNotIn('id="reading-order-undo"', self.client.get('/structure').text)

    def test_approved_button_disabled_and_review_tools_collapsed_without_deleting_cards(self):
        document = self.resolved_document()
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        page = self.client.get('/structure').text
        self.assertRegex(page, r'aria-label="Approve block 1" disabled>Approve')
        self.assertNotIn('aria-label="Approve block 3"', page)
        self.assertIn('aria-label="Save and approve block 3"', page)
        for tool in ('image-description-tools',):
            tag = re.search(r'<details id="' + tool + r'"[^>]*>', page).group()
            self.assertNotIn(' open', tag)
        self.assertIn('id="visual-chart"', page)
        self.assertIn('id="visual-description-tools"', page)
        self.assertIn('Standalone visual descriptions', page)
        self.assertIn('Choose Not applicable if short alt text is sufficient.', page)
        self.assertIn('href="/help#image-descriptions"', page)
        self.assertNotIn('Why these images appear here', page)
        self.assertEqual(page.count('id="visual-chart"'), 1)
        self.assertEqual(ensure_review_document(self.root)['review']['complex_visuals'], document['review']['complex_visuals'])

    def test_manual_import_has_ordered_steps(self):
        page = self.client.get('/structure').text
        instructions = re.search(r'id="draft-manual-import".*?<ol>(.*?)</ol>', page, re.S).group(1)
        self.assertEqual(instructions.count('<li>'), 4)
        self.assertLess(instructions.index('Validate responses'), instructions.index('Import drafts into image fields'))
