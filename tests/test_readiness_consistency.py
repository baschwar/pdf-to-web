"""Readiness decisions agree across persisted evidence and review surfaces."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import test_image_draft_routes as routes
from review_helpers import approve_publication_fixture, stamp_fixture_approvals
from pdf_to_web.accessibility import assess_document, visual_readiness
from pdf_to_web.publication import content_digest, effective_block_status, readiness_findings
from pdf_to_web.review_state import (
    REVIEW_SCHEMA, _restore_legacy_owner_approvals, block_review_reason,
    ensure_review_document, review_progress, save_review_document, update_block,
    update_complex_visual, undo_last,
)


class LegacyApprovalEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.history = self.root / 'review/revisions'
        self.history.mkdir(parents=True)
        self.document = {
            'schema_version': 'pdf-to-web-normalized-v1',
            'output_pages': {'project_id': 'synthetic-project'},
            'review_session': {'schema_version': REVIEW_SCHEMA,
                               'created_at': '2026-10-01T10:00:00Z',
                               'updated_at': '2026-10-01T12:00:00Z'},
            'blocks': [{'id': 'owner', 'type': 'list',
                        'review': {'status': 'approved', 'updated_at': '2026-10-01T11:00:00Z'},
                        'children': [{'id': 'item', 'type': 'list_item', 'content': 'Reviewed resource',
                                      'provenance': {'source_page': 11},
                                      'review': {'status': 'needs_review', 'updated_at': '2026-10-01T10:59:00Z'}}]}],
        }

    def snapshot(self, document=None, name='20261001T120000Z.json'):
        path = self.history / name
        path.write_text(json.dumps(document or self.document))
        return path

    def restore(self):
        return _restore_legacy_owner_approvals(self.root, self.document)

    def test_exact_proof_preserves_decisions_and_records_evidence(self):
        path = self.snapshot()
        before = copy.deepcopy(self.document['blocks'][0])
        self.assertTrue(self.restore())
        owner = self.document['blocks'][0]
        self.assertEqual(owner['children'], before['children'])
        self.assertEqual(owner['review']['status'], 'approved')
        self.assertEqual(owner['review']['updated_at'], before['review']['updated_at'])
        self.assertEqual(owner['review']['content_sha256'], content_digest(owner))
        self.assertEqual(owner['review']['approval_evidence']['snapshot_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(effective_block_status(owner), 'approved')
        self.assertFalse(self.restore())

    def test_no_history_remains_actionable_without_false_change_claim(self):
        self.assertFalse(self.restore())
        owner = self.document['blocks'][0]
        self.assertEqual(owner['review']['status'], 'approved')
        self.assertEqual(effective_block_status(owner), 'needs_review')
        self.assertEqual(review_progress(self.document)['needs_review'], 1)
        self.assertIn('cannot be verified', block_review_reason(owner))
        self.assertNotIn('changed after approval', block_review_reason(owner))
        self.assertEqual(readiness_findings(self.document)[0]['block_id'], 'owner')

    def test_foreign_identity_and_decision_times_do_not_prove_approval(self):
        for mutate in (
            lambda d: d['output_pages'].update(project_id='foreign'),
            lambda d: d['review_session'].update(created_at='2026-09-30T10:00:00Z'),
            lambda d: d['blocks'][0]['review'].update(updated_at='2026-10-01T10:58:00Z'),
            lambda d: d['review_session'].update(updated_at='invalid'),
            lambda d: d['blocks'][0]['review'].update(content_sha256='stale-stamp'),
        ):
            with self.subTest(mutate=mutate):
                prior = copy.deepcopy(self.document)
                mutate(prior)
                self.snapshot(prior)
                self.assertFalse(self.restore())
                self.assertNotIn('content_sha256', self.document['blocks'][0]['review'])

    def test_changed_content_provenance_and_exclusion_reject_old_proof(self):
        for mutate in (
            lambda b: b.update(content='Changed text'),
            lambda b: b['provenance'].update(source_page=12),
            lambda b: b.update(excluded=True),
            lambda b: b['review'].update(status='unreviewed'),
        ):
            with self.subTest(mutate=mutate):
                prior = copy.deepcopy(self.document)
                mutate(prior['blocks'][0]['children'][0])
                self.snapshot(prior)
                self.assertFalse(self.restore())

    def test_newer_revocation_or_corrupt_history_vetoes_older_match(self):
        self.snapshot(name='20261001T110100Z.json')
        newer = copy.deepcopy(self.document)
        newer['blocks'][0]['review']['status'] = 'needs_review'
        newest = self.snapshot(newer)
        self.assertFalse(self.restore())
        newest.write_text('{invalid')
        self.assertFalse(self.restore())

    def test_nested_or_duplicate_identity_is_not_top_level_proof(self):
        prior = copy.deepcopy(self.document)
        owner = prior['blocks'].pop()
        prior['blocks'] = [{'id': 'wrapper', 'type': 'list', 'children': [owner]}]
        self.snapshot(prior)
        self.assertFalse(self.restore())
        self.snapshot()
        self.document['blocks'][0]['children'].append(copy.deepcopy(self.document['blocks'][0]['children'][0]))
        self.assertFalse(self.restore())

    def test_child_changes_after_owner_decision_cannot_be_recovered(self):
        self.document['blocks'][0]['children'][0]['review']['updated_at'] = '2026-10-01T11:01:00Z'
        self.snapshot()
        self.assertFalse(self.restore())

    def test_snapshot_duplicate_descendant_under_another_owner_rejects_proof(self):
        prior = copy.deepcopy(self.document)
        prior['blocks'].append({'id': 'other-owner', 'type': 'list', 'children': [copy.deepcopy(prior['blocks'][0]['children'][0])]})
        self.snapshot(prior)
        self.assertFalse(self.restore())
        self.assertEqual(effective_block_status(self.document['blocks'][0]), 'needs_review')

    def test_history_filename_and_recorded_chronology_must_agree(self):
        approved = copy.deepcopy(self.document)
        approved['review_session']['updated_at'] = '2026-10-01T11:30:30Z'
        self.snapshot(approved, name='20261001T113030Z.json')
        revoked = copy.deepcopy(approved)
        revoked['review_session']['updated_at'] = '2026-10-01T11:30:35Z'
        revoked['blocks'][0]['review']['status'] = 'needs_review'
        self.snapshot(revoked, name='20261001T113025Z.json')
        self.assertFalse(self.restore())
        self.assertNotIn('content_sha256', self.document['blocks'][0]['review'])

    def test_symlink_history_is_not_used(self):
        path = self.snapshot()
        (self.history / '20261001T130000Z.json').symlink_to(path)
        self.assertFalse(self.restore())

    def test_fresh_approval_stamp_covers_nested_content_and_changes_invalidate(self):
        owner = self.document['blocks'][0]
        owner['review']['content_sha256'] = content_digest(owner)
        self.assertEqual(effective_block_status(owner), 'approved')
        owner['children'][0]['content'] = 'Changed after approval'
        self.assertEqual(effective_block_status(owner), 'needs_review')
        self.assertEqual(readiness_findings(self.document)[0]['code'], 'block_approval_changed')

    def test_diagnostic_related_owner_uses_effective_review_status(self):
        self.document['metadata'] = {'title': 'Synthetic list review', 'language': 'en'}
        self.document['review'] = {'issues': [{'code': 'block_review_required', 'message': 'Review source list', 'block_ids': ['owner']}]}
        report = assess_document(self.document)
        diagnostic = next(item for item in report['items'] if item['category'] == 'diagnostics')
        self.assertEqual(diagnostic['related_blocks'][0]['status'], 'needs_review')
        self.assertEqual(diagnostic['status'], 'unresolved')
        self.snapshot()
        self.assertTrue(self.restore())
        diagnostic = next(item for item in assess_document(self.document)['items'] if item['category'] == 'diagnostics')
        self.assertEqual(diagnostic['related_blocks'][0]['status'], 'approved')
        self.assertEqual(diagnostic['status'], 'resolved')


class ReadinessSurfaceTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def complete_text_pending_decision(self):
        document = approve_publication_fixture(self.root)
        visual = document['review']['complex_visuals'][0]
        visual.update(source_block_id='photo', status='reclassified')
        document['blocks'][2]['complex_visual_id'] = visual['id']
        stamp_fixture_approvals(document)
        save_review_document(self.root, document, snapshot=False)
        return ensure_review_document(self.root), visual

    def test_reclassified_description_is_pending_on_every_surface(self):
        document, visual = self.complete_text_pending_decision()
        readiness = visual_readiness(document, visual)
        self.assertTrue(readiness['text_complete'])
        self.assertFalse(readiness['review_complete'])
        self.assertFalse(readiness['complete'])
        self.assertEqual(document['blocks'][2]['review']['status'], 'approved')
        for route in ('/structure', '/document'):
            self.assertNotIn('id="structure-review-complete"', self.client.get(route).text)
        structure = self.client.get('/structure').text
        self.assertIn('1 image review', structure)
        self.assertIn('Text provided; awaiting manual review', structure)
        self.assertIn('data-review-status="needs_review"', structure)
        accessibility = self.client.get('/accessibility').text
        self.assertIn('Description needs manual review', accessibility)
        self.assertIn('#visual-chart', accessibility)
        self.assertIn('Open description', accessibility)
        export = self.client.get('/export').text
        self.assertIn('href="/structure#visual-chart">Description on source page 1:', export)
        self.assertIn('data-publication-ready="false"', export)

    def test_manual_decision_save_reopen_and_undo_keep_gate_consistent(self):
        document, visual = self.complete_text_pending_decision()
        update_complex_visual(self.root, visual['id'], {'status': 'reviewed'})
        reopened = ensure_review_document(self.root)
        self.assertTrue(visual_readiness(reopened, reopened['review']['complex_visuals'][0])['complete'])
        self.assertEqual(readiness_findings(reopened), [])
        self.assertIn('id="structure-review-complete"', self.client.get('/structure').text)
        undo_last(self.root)
        reopened = ensure_review_document(self.root)
        self.assertEqual(reopened['review']['complex_visuals'][0]['status'], 'reclassified')
        self.assertFalse(visual_readiness(reopened, reopened['review']['complex_visuals'][0])['complete'])

    def test_description_exceptions_and_reviewed_missing_text(self):
        document, visual = self.complete_text_pending_decision()
        for status in ('not_applicable', 'excluded'):
            visual['status'] = status
            self.assertTrue(visual_readiness(document, visual)['complete'])
        visual['status'] = 'reviewed'
        visual['accessibility']['long_description'] = ''
        visual['accessibility']['adjacent_text'] = ''
        self.assertFalse(visual_readiness(document, visual)['complete'])
        document['blocks'][2]['decorative'] = True
        self.assertTrue(visual_readiness(document, visual)['complete'])
        document['blocks'][2]['decorative'] = False
        document['blocks'][2]['review']['status'] = 'excluded'
        self.assertTrue(visual_readiness(document, visual)['complete'])

    def test_uncertain_owner_has_enabled_approval_and_readable_exact_export_link(self):
        document = approve_publication_fixture(self.root)
        owner = document['blocks'][1]
        owner.update(type='list', content='', children=[{'id': 'nested', 'type': 'list_item', 'content': 'Read the <resource>', 'review': {'status': 'needs_review', 'updated_at': '2026-10-01T10:00:00Z'}}])
        owner['review'].pop('content_sha256', None)
        save_review_document(self.root, document, snapshot=False)
        structure = self.client.get('/structure').text
        self.assertIn('id="block-p"', structure)
        self.assertRegex(structure, r'aria-label="Approve block 2">Approve')
        self.assertIn('Earlier approval cannot be verified', structure)
        export = self.client.get('/export').text
        self.assertIn('href="/structure#block-p">Source page unknown · Block 2: list —', export)
        self.assertIn('&lt;resource&gt;', export)
        update_block(self.root, 'p', {'review_status': 'approved'})
        self.assertEqual(effective_block_status(ensure_review_document(self.root)['blocks'][1]), 'approved')
        undo_last(self.root)
        self.assertEqual(effective_block_status(ensure_review_document(self.root)['blocks'][1]), 'needs_review')

    def test_excluded_ancestor_resolves_nested_image_description_everywhere(self):
        document, visual = self.complete_text_pending_decision()
        image = document['blocks'].pop(2)
        document['blocks'].append({'id': 'excluded-owner', 'type': 'list', 'review': {'status': 'excluded'}, 'children': [image]})
        save_review_document(self.root, document, snapshot=False)
        reopened = ensure_review_document(self.root)
        readiness = visual_readiness(reopened, reopened['review']['complex_visuals'][0])
        self.assertTrue(readiness['complete'])
        self.assertEqual(readiness['label'], 'Excluded')
        self.assertEqual(readiness_findings(reopened), [])
        self.assertIn('id="structure-review-complete"', self.client.get('/structure').text)
        self.assertNotIn('Description needs manual review', self.client.get('/accessibility').text)
        self.assertIn('data-publication-ready="true"', self.client.get('/export').text)
