"""Displayed image review and atomic Accessibility batches on synthetic projects."""
import copy
import re
import unittest
from unittest.mock import patch

import test_image_draft_routes as routes
from pdf_to_web.bulk_review import records
from pdf_to_web.export import export_project
from pdf_to_web.errors import PdfToWebError
from pdf_to_web.exporters import html, gutenberg
from pdf_to_web.image_review import descriptions_for, review_token
from pdf_to_web.publication import readiness_findings
from pdf_to_web.review_state import ensure_review_document, save_review_document, review_progress, undo_last, update_block, update_complex_visual


class UnifiedImageReviewTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def test_bulk_description_badges_distinguish_readiness_from_recorded_decision(self):
        for kind, expected_state, expected_label, recorded in (
            ('excluded', 'excluded', 'Excluded', 'Needs Text Equivalent'),
            ('decorative', 'not_applicable', 'Decorative image', 'Needs Text Equivalent'),
            ('incomplete', 'needs_review', 'Text equivalent needed', 'Reviewed'),
        ):
            with self.subTest(kind=kind):
                document = self.model(3)
                block = document['blocks'][3]
                visual = document['review']['complex_visuals'][2]
                if kind == 'excluded':
                    block['review']['status'] = 'excluded'
                elif kind == 'decorative':
                    block['decorative'] = True
                else:
                    visual['status'] = 'reviewed'
                    visual['accessibility']['long_description'] = ''
                save_review_document(self.root, document)
                before = (self.root / 'review/current.json').read_bytes()
                page = self.client.get('/accessibility').text
                rows = re.findall(r'<article class="bulk-review-row".*?</article>', page, re.S)
                row = next(r for r in rows if 'value="description:description-2"' in r)
                self.assertIn(f'class="block-status status-{expected_state}">{expected_label}</span>', row)
                self.assertIn('Recorded description decision: ' + recorded, row)
                self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def model(self, count=21):
        document = ensure_review_document(self.root)
        document['blocks'] = [{'id': 'title', 'type': 'heading', 'level': 1, 'content': 'Image review', 'review': {'status': 'approved'}}]
        document['review']['issues'] = []
        document['review']['complex_visuals'] = []
        for i in range(count):
            document['blocks'].append({'id': f'image-{i}', 'type': 'image', 'src': 'images/photo.png',
                'alt': f'Image purpose {i}', 'caption': f'Caption {i}', 'complex_visual_id': f'description-{i}',
                'provenance': {'source_page': 1, 'bounding_box': [10, 20, 300, 400]}, 'review': {'status': 'approved'}})
            document['review']['complex_visuals'].append({'id': f'description-{i}', 'type': 'image', 'source_block_id': f'image-{i}',
                'status': 'reviewed' if i < 2 else 'needs_text_equivalent', 'source_page': 1,
                'accessibility': {'short_alt': f'Image purpose {i}', 'long_description': f'Complete description {i}', 'adjacent_text': ''}})
        document.pop('output_pages', None)
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def approve(self, identity='image-2', **changes):
        document = ensure_review_document(self.root)
        block = next(b for b in document['blocks'] if b['id'] == identity)
        payload = {'expected_review_token': review_token(document), 'displayed_description_ids': [str(v['id']) for v in descriptions_for(document, block)], **changes}
        return self.client.post(f'/api/blocks/{identity}/save-and-approve', headers=self.headers, json=payload)

    def batch_payload(self, selected, status='reviewed', classification='Descriptions · image'):
        document = ensure_review_document(self.root)
        return {'project_id': document['output_pages']['project_id'], 'expected_review_token': review_token(document),
                'classification': classification, 'visible_ids': [r['id'] for r in records(document) if not classification or r['classification'] == classification],
                'selected_ids': selected, 'status': status}

    def batch(self, data):
        return self.client.post('/api/accessibility/bulk-review', headers=self.headers, json=data)

    def test_existing_21_images_19_pending_are_unchanged_on_read(self):
        before = self.model()
        self.assertEqual(review_progress(before)['pending_descriptions'], 19)
        data = (self.root / 'review/current.json').read_bytes()
        for path in ('/document', '/structure', '/accessibility', '/export'):
            page = self.client.get(path)
            self.assertEqual(page.status_code, 200)
            self.assertIn('19 description reviews', page.text)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), data)
        self.assertIn('Text provided; awaiting manual review', self.client.get('/structure').text)

    def test_explicit_one_image_approval_persists_scope_counts_provenance_and_undo(self):
        before = self.model()
        response = self.approve()
        self.assertEqual(response.status_code, 200, response.text)
        after = ensure_review_document(self.root)
        self.assertEqual(review_progress(after)['pending_descriptions'], 18)
        self.assertEqual(after['review']['complex_visuals'][2]['status'], 'reviewed')
        self.assertEqual(after['review']['complex_visuals'][3:], before['review']['complex_visuals'][3:])
        self.assertEqual(after['blocks'][3]['provenance'], before['blocks'][3]['provenance'])
        self.assertEqual(after['review_session']['revision'], before['review_session']['revision'] + 1)
        for path in ('/document', '/structure', '/accessibility', '/export'):
            self.assertIn('18 description reviews', self.client.get(path).text)
        self.assertEqual(ensure_review_document(self.root)['review'], after['review'])
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['review'], before['review'])
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])

    def test_incomplete_alt_and_long_reject_atomically(self):
        self.model()
        for changes in ({'alt': ''}, {'long_description': ''}):
            before = (self.root / 'review/current.json').read_bytes()
            result = self.approve(**changes)
            self.assertEqual(result.status_code, 400, result.text)
            self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_multiple_descriptions_are_visible_and_cannot_be_hidden_or_partly_approved(self):
        document = self.model()
        second = {'id': 'second', 'type': 'chart', 'source_block_id': 'image-2', 'status': 'reclassified',
                  'accessibility': {'short_alt': 'Image purpose 2', 'long_description': 'Second complete description'}}
        document['review']['complex_visuals'].append(second)
        save_review_document(self.root, document)
        page = self.client.get('/structure').text
        self.assertIn('data-visual-id="second"', page)
        before = (self.root / 'review/current.json').read_bytes()
        response = self.approve(displayed_description_ids=['description-2'])
        self.assertEqual(response.status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertEqual(self.approve().status_code, 200)
        after = ensure_review_document(self.root)
        self.assertEqual(after['review']['complex_visuals'][-1]['status'], 'reviewed')
        for markup in (html.render_document(after), gutenberg.render_document(after)):
            self.assertIn('Second complete description', markup)
            self.assertIn('Complete description 2', markup)

    def test_conflicting_and_missing_associations_cannot_be_approved(self):
        for conflict in ('other-source', 'duplicate', 'missing'):
            document = self.model()
            if conflict == 'other-source':
                document['review']['complex_visuals'][2]['source_block_id'] = 'image-3'
            elif conflict == 'duplicate':
                document['review']['complex_visuals'].append(copy.deepcopy(document['review']['complex_visuals'][2]))
            else:
                document['review']['complex_visuals'].pop(2)
            save_review_document(self.root, document)
            before = (self.root / 'review/current.json').read_bytes()
            self.assertEqual(self.approve().status_code, 400)
            self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_concurrent_edit_missing_token_and_changed_selection_reject_without_writes(self):
        document = self.model()
        token = review_token(document)
        update_block(self.root, 'image-3', {'caption': 'Concurrent change'})
        for changes in ({'expected_review_token': token}, {'expected_review_token': None}, {'displayed_description_ids': []}):
            before = (self.root / 'review/current.json').read_bytes()
            self.assertEqual(self.approve(**changes).status_code, 400)
            self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_ordinary_edits_and_stale_reviewed_select_invalidate(self):
        self.model()
        self.assertEqual(self.approve().status_code, 200)
        saved = update_block(self.root, 'image-2', {'caption': 'Material change', 'review_status': 'approved'})
        self.assertEqual(saved['blocks'][3]['review']['status'], 'needs_review')
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'reclassified')
        saved = update_complex_visual(self.root, 'description-2', {'long_description': 'Another material change', 'status': 'reviewed'})
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'reclassified')
        self.assertIn('description_review_pending', [i['code'] for i in readiness_findings(saved)])

    def test_save_without_approval_keeps_pending_and_new_description_needs_explicit_review(self):
        self.model()
        update_block(self.root, 'image-2', {'long_description': 'Saved draft', 'review_status': 'approved'})
        self.assertEqual(review_progress(ensure_review_document(self.root))['pending_descriptions'], 19)
        document = ensure_review_document(self.root)
        document['blocks'].append({'id': 'new-image', 'type': 'image', 'alt': 'New image', 'review': {'status': 'unreviewed'}})
        save_review_document(self.root, document)
        self.assertEqual(self.approve('new-image', long_description='New displayed description').status_code, 200)
        self.assertEqual(ensure_review_document(self.root)['review']['complex_visuals'][-1]['status'], 'reviewed')

    def test_decorative_and_excluded_remain_recoverable(self):
        before = self.model()
        self.assertEqual(self.approve(decorative=True, alt='', long_description='').status_code, 200)
        after = ensure_review_document(self.root)
        self.assertTrue(after['blocks'][3]['decorative'])
        self.assertEqual(after['review']['complex_visuals'][2]['status'], 'not_applicable')
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])
        update_block(self.root, 'image-2', {'review_status': 'excluded'})
        before_bytes = (self.root / 'review/current.json').read_bytes()
        self.assertEqual(self.approve().status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before_bytes)

    def test_description_batch_is_atomic_one_undo_and_export_gate_updates(self):
        before = self.model(4)
        with self.assertRaises(PdfToWebError):
            export_project(self.root, 'html')
        result = self.batch(self.batch_payload(['description:description-2', 'description:description-3']))
        self.assertEqual(result.status_code, 200, result.text)
        after = ensure_review_document(self.root)
        self.assertEqual(review_progress(after)['pending_tasks'], 0)
        self.assertEqual(after['review_session']['revision'], before['review_session']['revision'] + 1)
        paths = export_project(self.root, 'all')
        semantic = next(path for path in paths if path.suffix == '.html' and path.parent.name == 'html').read_text()
        import xml.etree.ElementTree as ET
        from pdf_to_web.exporters.wxr import CONTENT_NS
        xml = next(path for path in paths if path.suffix == '.xml')
        wordpress_content = ET.parse(xml).find('.//{' + CONTENT_NS + '}encoded').text
        for text in ('Complete description 2', 'Complete description 3'):
            self.assertEqual(semantic.count(text), 1)
            self.assertEqual(wordpress_content.count(text), 1)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['review'], before['review'])
        self.assertEqual(review_progress(ensure_review_document(self.root))['pending_descriptions'], 2)

    def test_batch_rejects_incomplete_item_without_partial_success(self):
        document = self.model(4)
        document['review']['complex_visuals'][3]['accessibility']['long_description'] = ''
        save_review_document(self.root, document)
        before = (self.root / 'review/current.json').read_bytes()
        result = self.batch(self.batch_payload(['description:description-2', 'description:description-3']))
        self.assertEqual(result.status_code, 400)
        self.assertIn('description-3', result.text)
        self.assertIn('No changes saved', result.text)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_batch_revalidates_scope_identity_states_permission_and_revision(self):
        self.model(4)
        base = self.batch_payload(['description:description-2'])
        for override in ({'project_id': 'other'}, {'visible_ids': []}, {'selected_ids': ['description:missing']},
                         {'selected_ids': ['description:description-2'] * 2}, {'status': 'approved'},
                         {'classification': 'Blocks · image'}, {'expected_review_token': 'stale'}):
            with self.subTest(override=override):
                before = (self.root / 'review/current.json').read_bytes()
                self.assertEqual(self.batch({**base, **override}).status_code, 400)
                self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertEqual(self.client.post('/api/accessibility/bulk-review', json=base).status_code, 403)
        mixed = self.batch_payload(['description:description-2', 'block:image-2'], classification='')
        self.assertIn('Select one record type', self.batch(mixed).text)
        document = ensure_review_document(self.root)
        document['review']['status'] = 'conversion_blocked'
        save_review_document(self.root, document)
        self.assertEqual(self.batch(self.batch_payload(['description:description-2'])).status_code, 409)

    def test_batch_image_approval_reviews_only_selected_image_descriptions(self):
        self.model()
        result = self.batch(self.batch_payload(['block:image-2'], status='approved', classification='Blocks · image'))
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(review_progress(ensure_review_document(self.root))['pending_descriptions'], 18)

    def test_write_failure_preserves_atomic_image_and_batch_undo_history(self):
        self.model()
        before = (self.root / 'review/current.json').read_bytes()
        snapshots = set((self.root / 'review/revisions').glob('*.json'))
        with patch('pdf_to_web.review_state.save_project', side_effect=OSError('Write failed')):
            self.assertEqual(self.approve().status_code, 400)
            self.assertEqual(self.batch(self.batch_payload(['description:description-2'])).status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertEqual(set((self.root / 'review/revisions').glob('*.json')), snapshots)

    def test_preview_label_bulk_grouping_and_back_to_top_preserved(self):
        self.model()
        preview = self.client.get('/preview').text
        self.assertIn('WSUWP (approximate preview)', preview)
        self.assertIn('href="/help#wordpress-preview"', self.client.get('/output-pages').text)
        self.assertIn('production WSU theme CSS', self.client.get('/help').text)
        page = self.client.get('/accessibility').text
        for text in ('Select all visible records', 'Review state options', 'Blocks · image', 'Descriptions · image', 'bulk-review-confirm'):
            self.assertIn(text, page)
        self.assertIn('back-to-top', page)

    def test_bulk_diagnostic_decision_does_not_approve_blocks_or_descriptions(self):
        document = self.model(4)
        document['review']['issues'] = [{'code': 'inspect_extraction', 'page': 1, 'message': 'Inspect the retained image extraction.'}]
        save_review_document(self.root, document)
        before = ensure_review_document(self.root)
        data = self.batch_payload(['decision:diagnostic:inspect_extraction:1'], 'approved', 'Decisions · diagnostics')
        result = self.batch(data)
        self.assertEqual(result.status_code, 200, result.text)
        after = ensure_review_document(self.root)
        self.assertEqual(after['blocks'], before['blocks'])
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])
        self.assertEqual(review_progress(after)['pending_descriptions'], 2)
        self.assertEqual(after['accessibility_review']['decisions']['diagnostic:inspect_extraction:1']['status'], 'approved')
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root).get('accessibility_review'), before.get('accessibility_review'))

    def test_prior_not_applicable_does_not_bypass_required_text_in_reviewed_batch(self):
        document = self.model(4)
        visual = document['review']['complex_visuals'][2]
        visual['status'] = 'not_applicable'
        visual['accessibility']['long_description'] = ''
        save_review_document(self.root, document)
        before = (self.root / 'review/current.json').read_bytes()
        result = self.batch(self.batch_payload(['description:description-2']))
        self.assertEqual(result.status_code, 400)
        self.assertIn('Text is missing', result.text)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_excluded_batch_record_cannot_be_reviewed_and_undo_retains_text(self):
        before = self.model(4)
        result = self.batch(self.batch_payload(['description:description-2'], 'excluded'))
        self.assertEqual(result.status_code, 200)
        excluded = (self.root / 'review/current.json').read_bytes()
        self.assertEqual(self.batch(self.batch_payload(['description:description-2'])).status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), excluded)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['review'], before['review'])

    def test_null_text_and_conflicting_editor_payloads_are_rejected(self):
        self.model(4)
        for changes in ({'alt': None}, {'description_edits': [{'id': 'description-2', 'long_description': 'Displayed', 'adjacent_text': ''}], 'long_description': 'Conflicting'}):
            before = (self.root / 'review/current.json').read_bytes()
            self.assertEqual(self.approve(**changes).status_code, 400)
            self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_invalid_association_is_pending_with_exact_targets_across_surfaces(self):
        document = self.model(4)
        document['blocks'][3]['complex_visual_id'] = 'missing-description'
        save_review_document(self.root, document)
        document = ensure_review_document(self.root)
        self.assertEqual(review_progress(document)['pending_blocks'], 2)
        self.assertIn('image_description_association_invalid', [item['code'] for item in readiness_findings(document)])
        for route in ('/document', '/structure', '/accessibility', '/export'):
            page = self.client.get(route)
            self.assertEqual(page.status_code, 200)
            self.assertIn('2 image reviews', page.text)
        self.assertIn('image-2', self.client.get('/export').text)

    def test_orphan_description_blocks_publication_instead_of_disappearing(self):
        document = self.model(4)
        document['review']['complex_visuals'][2]['source_block_id'] = 'missing-image'
        document['blocks'][3].pop('complex_visual_id')
        save_review_document(self.root, document)
        current = ensure_review_document(self.root)
        self.assertIn('description_source_missing', [finding['code'] for finding in readiness_findings(current)])
        with self.assertRaises(PdfToWebError):
            export_project(self.root, 'html')
        self.assertIn('source image is missing', self.client.get('/structure').text)

    def test_complex_editor_alt_change_invalidates_other_associated_reviews(self):
        document = self.model(4)
        document['review']['complex_visuals'].append({'id': 'second-description', 'type': 'chart', 'source_block_id': 'image-2',
            'status': 'reviewed', 'accessibility': {'short_alt': 'Image purpose 2', 'long_description': 'Additional details'}})
        document['review']['complex_visuals'][2]['status'] = 'reviewed'
        save_review_document(self.root, document)
        current = ensure_review_document(self.root)
        response = self.client.post('/api/complex-visuals/description-2', headers=self.headers,
            json={'short_alt': 'Changed image purpose', 'status': 'reviewed', 'expected_review_token': review_token(current)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['reload_required'])
        saved = ensure_review_document(self.root)
        self.assertEqual(saved['review']['complex_visuals'][2]['status'], 'reclassified')
        self.assertEqual(saved['review']['complex_visuals'][-1]['status'], 'reclassified')
        self.assertEqual(saved['review']['complex_visuals'][-1]['accessibility']['short_alt'], 'Changed image purpose')
