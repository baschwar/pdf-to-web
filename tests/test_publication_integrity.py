import copy
import json
import unittest
from unittest.mock import patch

import test_image_draft_routes as routes
from review_helpers import approve_publication_fixture
from pdf_to_web.errors import PdfToWebError
from pdf_to_web.export import export_project
from pdf_to_web.export_validation import validate_project_exports
from pdf_to_web.output_page_export import export_pages
from pdf_to_web.publication import findings, require_current_artifact
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, update_complex_visual, undo_last, _atomic_write
from pdf_to_web.media_mapping import apply_media_mapping


class PublicationIntegrityTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def test_changed_approval_reason_persists_clears_and_undo_restores(self):
        from pdf_to_web.accessibility import assess_document
        approve_publication_fixture(self.root)
        for block_id, changes in [('h', {'content': 'Edited title'}), ('p', {'content': 'Edited paragraph'})]:
            doc = ensure_review_document(self.root)
            if block_id == 'h':
                block_id = next(b['id'] for b in doc['blocks'] if b['type'] == 'heading')
            update_block(self.root, block_id, changes)
            update_block(self.root, block_id, {'review_status': 'needs_review'})
            doc = ensure_review_document(self.root)
            block = next(b for b in doc['blocks'] if b['id'] == block_id)
            self.assertEqual(block['review']['reason'], 'changed_after_approval')
            self.assertIn('changed after approval', self.client.get('/structure').text)
            item = next(i for i in assess_document(doc)['items'] if i['id'] == 'structure:' + block_id)
            self.assertIn('changed after approval', item['message'])
            update_block(self.root, block_id, {'review_status': 'approved'})
            self.assertNotIn('reason', next(b for b in ensure_review_document(self.root)['blocks'] if b['id'] == block_id)['review'])
            undo_last(self.root)
            self.assertEqual(next(b for b in ensure_review_document(self.root)['blocks'] if b['id'] == block_id)['review']['reason'], 'changed_after_approval')
            update_block(self.root, block_id, {'review_status': 'approved'})

    def test_nested_link_reason_belongs_to_approved_owner_not_new_child(self):
        doc = approve_publication_fixture(self.root)
        doc['blocks'][1] = {'id': 'p', 'type': 'list', 'content': 'Old label', 'children': [
            {'id': 'child', 'type': 'list_item', 'content': 'Old label', 'runs': [
                {'type': 'link', 'text': 'Old label', 'url': 'https://example.test/resource'}],
             'review': {'status': 'unreviewed'}}], 'review': {'status': 'needs_review'}}
        save_review_document(self.root, doc)
        update_block(self.root, 'p', {'review_status': 'approved'})
        update_block(self.root, 'child', {'link_index': 0, 'link_text': 'New label'})
        update_block(self.root, 'p', {'review_status': 'needs_review'})
        owner = ensure_review_document(self.root)['blocks'][1]
        self.assertEqual(owner['review']['reason'], 'changed_after_approval')
        self.assertNotIn('reason', owner['children'][0]['review'])
        self.assertEqual(owner['children'][0]['runs'][0]['url'], 'https://example.test/resource')
        undo_last(self.root)
        undo_last(self.root)
        owner = ensure_review_document(self.root)['blocks'][1]
        self.assertEqual(owner['review']['status'], 'approved')
        self.assertNotIn('reason', owner['review'])
        self.assertEqual(owner['children'][0]['content'], 'Old label')

    def test_never_approved_edits_and_manual_flags_do_not_claim_prior_approval(self):
        update_block(self.root, 'p', {'content': 'Never approved edit', 'review_status': 'approved'})
        block = ensure_review_document(self.root)['blocks'][1]
        self.assertEqual(block['review']['status'], 'needs_review')
        self.assertNotIn('reason', block['review'])
        update_block(self.root, 'p', {'review_status': 'approved'})
        update_block(self.root, 'p', {'review_status': 'needs_review'})
        block = ensure_review_document(self.root)['blocks'][1]
        self.assertNotIn('reason', block['review'])

    def export(self, target='html'):
        return self.client.post('/api/export', headers=self.headers, json={'target': target})

    def test_pending_all_public_formats_and_validator_fail_before_writing(self):
        for profile in ('generic', 'wsuwp'):
            for target in ('html', 'markdown', 'gutenberg', 'wordpress-xml', 'all'):
                with self.subTest(profile=profile, target=target), self.assertRaises(PdfToWebError):
                    export_project(self.root, target, profile)
        with self.assertRaises(PdfToWebError):
            export_pages(self.root)
        report, _ = validate_project_exports(self.root)
        data = json.loads(report.read_text())
        self.assertEqual(data['result'], 'FAIL')
        self.assertTrue(all(not f['generated'] for f in data['formats'].values()))
        self.assertFalse(list((self.root / 'output/html').glob('*.html')))
        self.assertTrue(export_project(self.root, 'accessibility'))

    def test_stale_download_blocked_after_edit_and_reapproval_until_regeneration(self):
        approve_publication_fixture(self.root)
        first = self.export()
        self.assertEqual(first.status_code, 200, first.text)
        url = first.json()['downloads'][0]['url']
        self.assertEqual(self.client.get(url).status_code, 200)
        update_block(self.root, 'p', {'content': 'Updated approved source', 'review_status': 'approved'})
        self.assertEqual(self.client.get(url).status_code, 409)
        update_block(self.root, 'p', {'review_status': 'approved'})
        self.assertEqual(self.client.get(url).status_code, 409)
        self.assertEqual(self.export().status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertIn('Updated approved source', self.client.get(url).text)

    def test_revised_state_with_same_revision_cannot_authorize_old_artifact(self):
        approve_publication_fixture(self.root)
        path = export_project(self.root, 'html')[0]
        doc = ensure_review_document(self.root)
        doc['metadata']['title'] = 'Different title with same revision'
        (self.root / 'review/current.json').write_text(json.dumps(doc))
        with self.assertRaises(PdfToWebError):
            require_current_artifact(self.root, str(path.relative_to(self.root)))

    def test_page_approval_gate_and_complete_positive_package(self):
        doc = approve_publication_fixture(self.root)
        export_pages(self.root)
        doc['output_pages']['pages'][0]['approval']['status'] = 'needs_review'
        save_review_document(self.root, doc)
        with self.assertRaisesRegex(PdfToWebError, 'Output page'):
            export_pages(self.root)
        self.assertEqual(self.client.get('/download/output/pages.zip').status_code, 409)
        # Whole-document exports do not require an optional arrangement decision.
        self.assertEqual(self.export().status_code, 200)

    def test_nested_list_owner_requires_reapproval_after_child_edit(self):
        doc = approve_publication_fixture(self.root)
        doc['blocks'][1] = {'id': 'p', 'type': 'list', 'content': 'First', 'children': [
            {'id': 'item', 'type': 'list_item', 'content': 'First', 'children': [], 'review': {'status': 'unreviewed'}}], 'review': {'status': 'approved'}}
        save_review_document(self.root, doc)
        update_block(self.root, 'p', {'review_status': 'approved'})
        self.assertEqual(findings(ensure_review_document(self.root)), [])
        # Child labels use the existing dedicated link editor.
        doc = ensure_review_document(self.root)
        doc['blocks'][1]['children'][0]['runs'] = [{'type': 'link', 'text': 'First', 'url': 'https://example.test'}]
        save_review_document(self.root, doc)
        update_block(self.root, 'p', {'review_status': 'approved'})
        update_block(self.root, 'item', {'link_index': 0, 'link_text': 'Changed'})
        self.assertTrue(any('Block p' in f for f in findings(ensure_review_document(self.root))))
        update_block(self.root, 'p', {'review_status': 'approved'})
        self.assertEqual(findings(ensure_review_document(self.root)), [])

    def test_edited_reviewed_description_requires_fresh_manual_decision(self):
        doc = approve_publication_fixture(self.root)
        visual = doc['review']['complex_visuals'][0]
        update_complex_visual(self.root, visual['id'], {'status': 'reviewed', 'long_description': 'Changed description'})
        current = ensure_review_document(self.root)
        self.assertEqual(current['review']['complex_visuals'][0]['status'], 'reclassified')
        self.assertTrue(any('Description' in f for f in findings(current)))
        update_complex_visual(self.root, visual['id'], {'status': 'reviewed'})
        self.assertEqual(ensure_review_document(self.root)['review']['complex_visuals'][0]['status'], 'reviewed')

    def test_stale_csv_cannot_replace_text_with_older_or_empty_values(self):
        approve_publication_fixture(self.root)
        before = copy.deepcopy(ensure_review_document(self.root)['blocks'][2])
        for alt, caption in [('Old alternative', 'Old caption'), ('', '')]:
            apply_media_mapping(self.root, 'block_id,wordpress_url,alt_text,caption\nphoto,https://example.test/photo.png,' + alt + ',' + caption + '\n')
            after = ensure_review_document(self.root)['blocks'][2]
            self.assertEqual((after.get('alt'), after.get('caption')), (before.get('alt'), before.get('caption')))

    def test_undo_current_write_failure_retains_state_and_snapshot_for_retry(self):
        update_block(self.root, 'p', {'content': 'Edit'})
        path = self.root / 'review/current.json'
        before = path.read_bytes()
        snapshots = sorted((self.root / 'review/revisions').glob('*.json'))
        def fail_current(target, data):
            if target == path:
                raise OSError('injected current write failure')
            return _atomic_write(target, data)
        with patch('pdf_to_web.review_state._atomic_write', side_effect=fail_current), self.assertRaises(OSError):
            undo_last(self.root)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(sorted((self.root / 'review/revisions').glob('*.json')), snapshots)
        undo_last(self.root)
        self.assertNotEqual(path.read_bytes(), before)

    def test_undo_project_write_failure_rolls_back_and_retains_retry(self):
        update_block(self.root, 'p', {'content': 'Edit'})
        path = self.root / 'review/current.json'
        before, project = path.read_bytes(), (self.root / 'project.json').read_bytes()
        snapshots = sorted((self.root / 'review/revisions').glob('*.json'))
        with patch('pdf_to_web.review_state.save_project', side_effect=OSError('injected project write failure')), self.assertRaises(OSError):
            undo_last(self.root)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual((self.root / 'project.json').read_bytes(), project)
        self.assertEqual(sorted((self.root / 'review/revisions').glob('*.json')), snapshots)
        undo_last(self.root)

    def linked_list(self):
        doc = ensure_review_document(self.root)
        children = [{'id': 'one', 'type': 'list_item', 'content': 'First', 'runs': [{'type': 'link', 'text': 'First', 'url': 'https://example.test/first'}], 'children': [], 'provenance': {'source_page': 2}},
                    {'id': 'two', 'type': 'list_item', 'content': 'Second', 'children': [], 'provenance': {'source_page': 3}}]
        doc['blocks'][1] = {'id': 'p', 'type': 'list', 'ordered': True, 'start': 4, 'content': 'First\nSecond', 'children': children}
        save_review_document(self.root, doc)
        return children

    def test_list_insert_reorder_delete_preserves_exact_item_identity(self):
        children = self.linked_list()
        update_block(self.root, 'p', {'content': 'New step\nSecond\nFirst'})
        items = ensure_review_document(self.root)['blocks'][1]['children']
        self.assertNotIn(items[0]['id'], {'one', 'two'})
        self.assertNotIn('runs', items[0])
        self.assertEqual(items[1:], [children[1], children[0]])
        update_block(self.root, 'p', {'content': 'First\nSecond'})
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['children'], children)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['children'][0]['id'], items[0]['id'])

    def test_resource_label_and_suffix_have_exact_link_boundary(self):
        self.linked_list()
        doc = ensure_review_document(self.root)
        item = doc['blocks'][1]['children'][0]
        item['content'] = 'Resources:(https://example.test/first)'
        item['runs'] = [{'type': 'strong', 'text': 'Resources:'}, {'type': 'text', 'text': '('}, {'type': 'link', 'text': 'https://example.test/first', 'url': 'https://example.test/first'}, {'type': 'text', 'text': ')'}]
        doc['blocks'][1]['content'] = item['content'] + '\nSecond'
        save_review_document(self.root, doc)
        update_block(self.root, 'p', {'content': 'Resources:(Visit resource library) now\nSecond'})
        runs = ensure_review_document(self.root)['blocks'][1]['children'][0]['runs']
        self.assertEqual(next(r['text'] for r in runs if r['type'] == 'link'), 'Visit resource library')
        self.assertEqual(runs[-1]['text'], ') now')

    def test_encoded_download_aliases_obey_canonical_publication_gate(self):
        approve_publication_fixture(self.root)
        response = self.export()
        filename = response.json()['files'][0].rsplit('/', 1)[1]
        update_block(self.root, 'p', {'content': 'Pending edit'})
        for alias in ('..%2F..%2F', '%2E%2E/%2E%2E/'):
            url = '/download/output/wordpress/reports/' + alias + 'html/' + filename
            self.assertEqual(self.client.get(url).status_code, 409)
        self.assertEqual(self.client.get('/download/output/%2E%2E/project.json').status_code, 404)

    def test_normal_http_page_review_unlocks_individual_and_package_exports(self):
        document = approve_publication_fixture(self.root)
        page_id = document['output_pages']['pages'][0]['id']
        document['output_pages']['pages'][0]['approval']['status'] = 'needs_review'
        save_review_document(self.root, document)
        reviewed = self.client.post('/api/output-pages/approve', headers=self.headers, json={'page_id': page_id})
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        self.assertEqual(ensure_review_document(self.root)['output_pages']['pages'][0]['approval']['status'], 'reviewed')
        for selected in (page_id, None):
            response = self.client.post('/api/output-pages/export', headers=self.headers, json={'page_id': selected})
            self.assertEqual(response.status_code, 200, response.text)
            for download in response.json()['downloads']:
                self.assertEqual(self.client.get(download['url']).status_code, 200, download['url'])

    def test_footnote_body_edit_updates_exported_text_and_undo_restores_both(self):
        document = approve_publication_fixture(self.root)
        document['blocks'].append({'id': 'note-body', 'type': 'paragraph', 'content': '1. Original footnote',
            'footnote_body_id': 'fn-1', 'export_as_footnote_body': True, 'provenance': {'raw': {'footnote marker': '1', 'footnote text': 'Original footnote'}}, 'review': {'status': 'approved'}})
        document['footnotes'] = [{'id': 'fn-1', 'marker': '1', 'text': 'Original footnote', 'references': []}]
        document['output_pages']['pages'][0]['block_ids'].append('note-body')
        save_review_document(self.root, document)
        approve_publication_fixture(self.root)
        update_block(self.root, 'note-body', {'content': '1. Corrected footnote'})
        current = ensure_review_document(self.root)
        self.assertEqual(current['footnotes'][0]['text'], 'Corrected footnote')
        self.assertTrue(any('note-body' in finding for finding in findings(current)))
        update_block(self.root, 'note-body', {'review_status': 'approved'})
        for target in ('html', 'markdown', 'gutenberg', 'wordpress-xml'):
            markup = export_project(self.root, target)[0].read_text()
            self.assertIn('Corrected footnote', markup)
            self.assertNotIn('Original footnote', markup)
        approve_publication_fixture(self.root)
        export_pages(self.root)
        self.assertIn('Corrected footnote', (self.root / 'output/pages/guide.html').read_text())
        # First Undo restores approval, second restores the body and derived note.
        undo_last(self.root)
        undo_last(self.root)
        restored = ensure_review_document(self.root)
        self.assertEqual(restored['blocks'][-1]['content'], '1. Original footnote')
        self.assertEqual(restored['footnotes'][0]['text'], 'Original footnote')

    def test_compound_resource_edit_preserves_unchanged_trailing_emphasis(self):
        document = ensure_review_document(self.root)
        paragraph = document['blocks'][1]
        paragraph['content'] = 'Resources: (https://example.test/help) Read carefully'
        paragraph['runs'] = [{'type': 'strong', 'text': 'Resources: '}, {'type': 'text', 'text': '('},
            {'type': 'link', 'text': 'https://example.test/help', 'url': 'https://example.test/help'},
            {'type': 'text', 'text': ') '}, {'type': 'emphasis', 'text': 'Read carefully'}]
        save_review_document(self.root, document)
        update_block(self.root, 'p', {'content': 'Resources: (Visit helpdesk) now Read carefully'})
        runs = ensure_review_document(self.root)['blocks'][1]['runs']
        self.assertIn({'type': 'emphasis', 'text': 'Read carefully'}, runs)
        self.assertEqual(next(r['text'] for r in runs if r['type'] == 'link'), 'Visit helpdesk')

    def test_manual_list_reorder_keeps_start_despite_original_source_numbers(self):
        self.linked_list()
        document = ensure_review_document(self.root)
        block = document['blocks'][1]
        block['children'][0]['provenance']['raw'] = {'content': '4. First'}
        block['children'][1]['provenance']['raw'] = {'content': '5. Second'}
        save_review_document(self.root, document)
        update_block(self.root, 'p', {'content': 'Second\nFirst'})
        reopened = ensure_review_document(self.root)['blocks'][1]
        self.assertEqual(reopened['start'], 4)
        self.assertEqual([b['id'] for b in reopened['children']], ['two', 'one'])
        self.assertEqual(reopened['children'][0]['provenance']['raw']['content'], '5. Second')
        undo_last(self.root)
        restored = ensure_review_document(self.root)['blocks'][1]
        self.assertEqual(restored['start'], 4)
        self.assertNotIn('manual_list_edit', restored.get('normalization', {}))

    def test_reopening_changed_stamped_content_makes_pending_review_actionable(self):
        document = approve_publication_fixture(self.root)
        document['blocks'][1]['content'] = 'Content changed during a repair'
        (self.root / 'review/current.json').write_text(json.dumps(document))
        reopened = ensure_review_document(self.root)
        self.assertEqual(reopened['blocks'][1]['review']['status'], 'needs_review')
        self.assertTrue(any('Block p' in finding for finding in findings(reopened)))
        update_block(self.root, 'p', {'review_status': 'approved'})
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['review']['status'], 'approved')

    def test_unmarked_footnote_prose_preserves_natural_leading_words_and_undo(self):
        document = approve_publication_fixture(self.root)
        document['blocks'].append({'id': 'note-body', 'type': 'paragraph', 'content': 'OLD FOOTNOTE',
            'footnote_body_id': 'fn-1', 'export_as_footnote_body': True,
            'provenance': {'raw': {'footnote marker': '1', 'footnote text': 'OLD FOOTNOTE'}}, 'review': {'status': 'approved'}})
        document['footnotes'] = [{'id': 'fn-1', 'marker': '1', 'text': 'OLD FOOTNOTE', 'references': []}]
        document['output_pages']['pages'][0]['block_ids'].append('note-body')
        save_review_document(self.root, document)
        for content in ('NEW FOOTNOTE', 'The current footnote.', 'For more context.'):
            with self.subTest(content=content):
                update_block(self.root, 'note-body', {'content': content})
                current = ensure_review_document(self.root)
                self.assertEqual(current['footnotes'][0]['text'], content)
                self.assertEqual(current['footnotes'][0]['marker'], '1')
                self.assertEqual(current['blocks'][-1]['provenance']['raw']['footnote text'], 'OLD FOOTNOTE')
                update_block(self.root, 'note-body', {'review_status': 'approved'})
                approve_publication_fixture(self.root)
                markup = export_project(self.root, 'html')[0].read_text()
                self.assertIn(content, markup)
                self.assertNotIn('OLD FOOTNOTE', markup)
                undo_last(self.root)
                undo_last(self.root)
                self.assertEqual(ensure_review_document(self.root)['footnotes'][0]['text'], 'OLD FOOTNOTE')
