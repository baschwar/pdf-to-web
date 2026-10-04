"""Independent scope/count checks: completed content can retain link judgments."""
import unittest

import test_image_draft_routes as routes
import test_unified_image_review as images
from pdf_to_web.accessibility import assess_document, save_decision, write_reports
from pdf_to_web.image_review import review_token
from pdf_to_web.publication import readiness_findings
from pdf_to_web.review_state import ensure_review_document, review_progress, save_review_document, undo_last


class IndependentAccessibilityScopeTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp
    image_model = images.UnifiedImageReviewTests.model

    def model(self):
        document = self.image_model(2)
        for i in range(4):
            url = f'https://example.test/instruction-{i}'
            document['blocks'].append({'id': f'link-block-{i}', 'type': 'paragraph', 'content': url,
                'runs': [{'type': 'link', 'text': url, 'url': url}], 'review': {'status': 'approved'},
                'provenance': {'source_page': i + 1}})
        document['review']['issues'] = [{'code': 'block_review_required', 'page': 1,
            'message': 'Historical extraction hierarchy judgment.', 'block_ids': ['title']}]
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def payload(self, scope='pending', classification='Decisions · links', status='approved', selected=None):
        from pdf_to_web.bulk_review import records
        document = ensure_review_document(self.root)
        rows = records(document)
        shown = [r for r in rows if (not classification or r['classification'] == classification)
                 and (scope == 'all' or bool(r['pending']) == (scope == 'pending'))]
        return {'project_id': document['output_pages']['project_id'], 'expected_review_token': review_token(document),
                'classification': classification, 'review_scope': scope, 'visible_ids': [r['id'] for r in shown],
                'selected_ids': selected if selected is not None else [r['id'] for r in shown], 'status': status}

    def batch(self, payload):
        return self.client.post('/api/accessibility/bulk-review', headers=self.headers, json=payload)

    def test_four_link_judgments_remain_independent_of_completed_content(self):
        document = self.model()
        self.assertEqual(review_progress(document)['pending_tasks'], 0)
        report = assess_document(document)
        self.assertEqual((report['summary']['unresolved'], report['summary']['resolved']), (4, 1))
        self.assertEqual({i['category'] for i in report['items'] if i['status'] == 'unresolved'}, {'links'})
        self.assertTrue(all(i['decision_allowed'] for i in report['items'] if i['status'] == 'unresolved'))

    def test_all_four_findings_keep_exact_owner_links_and_read_only_views(self):
        self.model()
        before = (self.root / 'review/current.json').read_bytes()
        page = self.client.get('/accessibility').text
        for i in range(4):
            self.assertIn(f'/structure#block-link-block-{i}', page)
        for route in ('/document', '/structure', '/accessibility', '/export'):
            self.assertEqual(self.client.get(route).status_code, 200)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_completed_content_does_not_silently_resolve_accessibility_reports(self):
        document = self.model()
        self.assertEqual(readiness_findings(document), [])
        paths = write_reports(self.root, document)
        html = next(p for p in paths if p.suffix == '.html').read_text()
        self.assertIn('4 unresolved', html)
        self.assertEqual(html.count('URL used as link text'), 4)
        self.assertEqual(assess_document(ensure_review_document(self.root))['summary']['unresolved'], 4)

    def test_recorded_exception_is_explicit_persistent_and_undoable(self):
        document = self.model()
        save_decision(document, 'link:link-block-0:1', 'approved', 'Visible URL is required in this instruction.')
        save_review_document(self.root, document)
        reopened = ensure_review_document(self.root)
        self.assertEqual(assess_document(reopened)['summary']['unresolved'], 3)
        self.assertEqual(review_progress(reopened)['pending_tasks'], 0)
        undo_last(self.root)
        self.assertEqual(assess_document(ensure_review_document(self.root))['summary']['unresolved'], 4)

    def test_default_visible_scope_contains_only_four_pending_decisions(self):
        from pdf_to_web.bulk_review import records, visible_records
        document = self.model()
        catalog = records(document)
        self.assertEqual(len(catalog), 13)
        visible = visible_records(document)
        self.assertEqual(len(visible), 4)
        self.assertTrue(all(r['kind'] == 'decision' and r['pending'] for r in visible))
        self.assertEqual(len(visible_records(document, review_scope='completed')), 9)
        self.assertEqual(len(visible_records(document, review_scope='all')), 13)
        self.assertEqual(visible_records(document, 'Blocks · image'), [])

    def test_pending_scope_batch_resolves_only_selected_judgments_and_one_undo(self):
        before = self.model()
        payload = self.payload(selected=['decision:link:link-block-0:1', 'decision:link:link-block-1:1'])
        response = self.batch(payload)
        self.assertEqual(response.status_code, 200, response.text)
        saved = ensure_review_document(self.root)
        self.assertEqual(assess_document(saved)['summary']['unresolved'], 2)
        self.assertEqual(saved['blocks'], before['blocks'])
        self.assertEqual(saved['review']['complex_visuals'], before['review']['complex_visuals'])
        self.assertEqual(saved['review_session']['revision'], before['review_session']['revision'] + 1)
        undo_last(self.root)
        self.assertEqual(assess_document(ensure_review_document(self.root))['summary']['unresolved'], 4)

    def test_hidden_completed_target_scope_mismatch_and_invalid_scope_reject_atomically(self):
        self.model()
        base = self.payload()
        for change in ({'selected_ids': ['block:image-0']}, {'review_scope': 'completed'},
                       {'review_scope': 'invalid'}, {'visible_ids': base['visible_ids'][:-1]},
                       {'project_id': 'different-project'}, {'expected_review_token': 'stale'}):
            with self.subTest(change=change):
                before = (self.root / 'review/current.json').read_bytes()
                response = self.batch({**base, **change})
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_completed_scope_explicitly_reopens_one_decision_and_preserves_content(self):
        document = self.model()
        save_decision(document, 'link:link-block-0:1', 'approved', 'Recorded manual judgment.')
        save_review_document(self.root, document)
        before = ensure_review_document(self.root)
        payload = self.payload(scope='completed', status='unresolved')
        self.assertEqual(payload['selected_ids'], ['decision:link:link-block-0:1'])
        response = self.batch(payload)
        self.assertEqual(response.status_code, 200, response.text)
        saved = ensure_review_document(self.root)
        self.assertEqual(assess_document(saved)['summary']['unresolved'], 4)
        self.assertEqual(saved['blocks'], before['blocks'])

    def test_manual_findings_keep_completion_gate_closed_before_or_after_browser_scan(self):
        self.model()
        page = self.client.get('/accessibility').text
        self.assertRegex(page, r'id="accessibility-complete"[^>]*data-document-ready="false"')
        self.assertEqual(assess_document(ensure_review_document(self.root))['summary']['unresolved'], 4)

    def test_reviewed_but_incomplete_description_stays_pending_in_visible_scope(self):
        from pdf_to_web.bulk_review import visible_records
        document = self.model()
        document['review']['complex_visuals'][0]['accessibility']['long_description'] = ''
        save_review_document(self.root, document)
        rows = visible_records(ensure_review_document(self.root))
        self.assertIn('description:description-0', [r['id'] for r in rows])
        self.assertIn('block:image-0', [r['id'] for r in rows])

    def test_scoped_api_still_requires_session_csrf_and_edit_permission(self):
        self.model()
        payload = self.payload()
        before = (self.root / 'review/current.json').read_bytes()
        self.assertEqual(self.client.post('/api/accessibility/bulk-review', json=payload).status_code, 403)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        document = ensure_review_document(self.root)
        document['review']['status'] = 'conversion_blocked'
        save_review_document(self.root, document)
        before = (self.root / 'review/current.json').read_bytes()
        self.assertEqual(self.batch(self.payload()).status_code, 409)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
