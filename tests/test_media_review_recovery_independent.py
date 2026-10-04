"""Independent evidence-gated restoration of existing media-only approvals."""
import copy
import json
import unittest
from unittest.mock import patch

import test_export_media_journey_independent as journey
from pdf_to_web import publication, media_review_recovery
from pdf_to_web.image_review import descriptions_for, review_token
from pdf_to_web.review_state import ensure_review_document, save_review_document, undo_last, update_block


class IndependentMediaReviewRecoveryTests(unittest.TestCase):
    setUp = journey.IndependentExportMediaJourneyTests.setUp
    image_model = journey.IndependentExportMediaJourneyTests.image_model
    media_xml = journey.IndependentExportMediaJourneyTests.media_xml
    prepare = journey.IndependentExportMediaJourneyTests.prepare
    match = journey.IndependentExportMediaJourneyTests.match

    def model(self, count=21, approve_first=True):
        if getattr(self, '_has_recovery_fixture', False):
            self.setUp()
        self._has_recovery_fixture = True
        # Seed a coherent synthetic session before the fixed approval/event dates.
        # These files belong only to this temporary test project.
        for path in [self.root / 'review/current.json', *sorted((self.root / 'review/revisions').glob('*.json'))]:
            value = json.loads(path.read_text())
            value['review_session']['created_at'] = '2026-10-04T03:00:00+00:00'
            value['review_session']['updated_at'] = '2026-10-04T03:00:00+00:00'
            path.write_text(json.dumps(value))
        with patch('pdf_to_web.review_state.utc_now', return_value='2026-10-04T04:00:00+00:00'):
            journey.IndependentExportMediaJourneyTests.model(self, count)
            self.prepare()
        self.original = copy.deepcopy(ensure_review_document(self.root))
        # The reused image fixture replaces its initial output-page identity.
        # Retain only evidence from this synthetic project's current identity.
        identity = self.original['output_pages']['project_id']
        for path in (self.root / 'review/revisions').glob('*.json'):
            if json.loads(path.read_text()).get('output_pages', {}).get('project_id') != identity:
                path.unlink()
        digest = publication.content_digest
        def old_digest(block, **unused):
            return digest(block, include_media_mapping=True)
        with patch.object(publication, 'content_digest', old_digest), patch('pdf_to_web.review_state.utc_now', return_value='2026-10-04T04:26:37+00:00'):
            response = self.match()
            self.assertEqual(response.status_code, 200, response.text)
        self.event = copy.deepcopy(ensure_review_document(self.root))
        if approve_first:
            document = ensure_review_document(self.root)
            block = next(b for b in document['blocks'] if b['id'] == 'image-0')
            payload = {'expected_review_token': review_token(document),
                       'displayed_description_ids': [v['id'] for v in descriptions_for(document, block)]}
            with patch('pdf_to_web.review_state.utc_now', return_value='2026-10-04T04:30:00+00:00'), patch('pdf_to_web.project.utc_now', return_value='2026-10-04T04:30:00+00:00'):
                response = self.client.post('/api/blocks/image-0/save-and-approve', headers=self.headers, json=payload)
                self.assertEqual(response.status_code, 200, response.text)
        return ensure_review_document(self.root)

    def stored_files(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in [self.root / 'project.json', self.root / 'review/current.json', *sorted((self.root / 'review/revisions').glob('*.json'))]}

    def mutate_later(self, identity, changes, when='2026-10-04T04:40:00+00:00'):
        with patch('pdf_to_web.review_state.utc_now', return_value=when):
            return update_block(self.root, identity, changes)

    def plan(self):
        from pdf_to_web.media_review_recovery import plan_recovery
        return plan_recovery(self.root, ensure_review_document(self.root))

    def payload(self):
        plan = self.plan()
        return {'token': plan['token'], 'project_id': plan['project_id'],
                'block_ids': [row['block_id'] for row in plan['rows']]}

    def apply(self, payload=None):
        from pdf_to_web.media_review_recovery import apply_recovery
        return apply_recovery(self.root, self.payload() if payload is None else payload)

    def test_proof_plan_excludes_new_approval_and_changes_no_saved_files(self):
        before = self.model()
        stored = self.stored_files()
        plan = self.plan()
        self.assertEqual({row['block_id'] for row in plan['rows']}, {f'image-{i}' for i in range(1, 21)})
        for row in plan['rows']:
            original = next(b for b in self.original['blocks'] if b['id'] == row['block_id'])
            self.assertEqual(row['approved_at'], original['review']['updated_at'])
        self.assertEqual(self.stored_files(), stored)
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['review'], before['blocks'][1]['review'])

    def test_explicit_recovery_restores_original_dates_keeps_new_review_maps_and_one_undo(self):
        before = self.model()
        after, count = self.apply()
        self.assertEqual(count, 20)
        self.assertEqual(after['review_session']['revision'], before['review_session']['revision'] + 1)
        self.assertEqual(after['blocks'][1], before['blocks'][1])
        for block in after['blocks'][2:22]:
            prior = next(b for b in before['blocks'] if b['id'] == block['id'])
            original = next(b for b in self.original['blocks'] if b['id'] == block['id'])
            self.assertEqual(block['review']['status'], 'approved')
            self.assertEqual(block['review']['updated_at'], original['review']['updated_at'])
            self.assertEqual({k: v for k, v in block.items() if k != 'review'}, {k: v for k, v in prior.items() if k != 'review'})
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])
        undo_last(self.root)
        restored = ensure_review_document(self.root)
        self.assertEqual(restored['blocks'], before['blocks'])
        self.assertEqual(restored['review']['complex_visuals'], before['review']['complex_visuals'])
        # Undo consumes a snapshot: final equality alone must not bypass the
        # contiguous-history proof or silently restore these approvals again.
        stored = self.stored_files()
        self.assertEqual(self.plan()['rows'], [])
        with self.assertRaises(ValueError):
            self.apply()
        self.assertEqual(self.stored_files(), stored)

    def test_current_api_preview_is_read_only_and_confirmation_is_explicit(self):
        self.model(3)
        stored = self.stored_files()
        response = self.client.get('/api/media-review-recovery')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual({r['block_id'] for r in response.json()['rows']}, {'image-1', 'image-2'})
        self.assertEqual(self.stored_files(), stored)
        payload = self.payload()
        self.assertEqual(self.client.post('/api/media-review-recovery', json=payload).status_code, 403)
        self.assertEqual(self.stored_files(), stored)
        applied = self.client.post('/api/media-review-recovery', headers=self.headers, json=payload)
        self.assertEqual(applied.status_code, 200, applied.text)
        self.assertEqual(ensure_review_document(self.root)['blocks'][2]['review']['status'], 'approved')

    def test_scope_token_identity_duplicates_and_hidden_new_approval_reject_without_writes(self):
        self.model(3)
        base = self.payload()
        for changes in ({'token': 'stale'}, {'project_id': 'different-project'}, {'block_ids': ['image-1']},
                        {'block_ids': ['image-1', 'image-2', 'image-0']}, {'block_ids': ['image-1', 'image-1']},
                        {'block_ids': ['image-1', 'missing']}, {'block_ids': []}):
            with self.subTest(changes=changes):
                stored = self.stored_files()
                with self.assertRaises(ValueError):
                    self.apply({**base, **changes})
                self.assertEqual(self.stored_files(), stored)

    def test_concurrent_current_edit_rejects_entire_old_scope(self):
        self.model(3)
        payload = self.payload()
        self.mutate_later('image-1', {'caption': 'Concurrent genuine edit.'})
        stored = self.stored_files()
        with self.assertRaises(ValueError):
            self.apply(payload)
        self.assertEqual(self.stored_files(), stored)
        self.assertEqual({r['block_id'] for r in self.plan()['rows']}, {'image-2'})

    def test_history_hash_change_rejects_old_preview_token(self):
        self.model(3)
        payload = self.payload()
        history = sorted((self.root / 'review/revisions').glob('*.json'))[0]
        history.write_bytes(history.read_bytes() + b'\n')
        stored = self.stored_files()
        with self.assertRaises(ValueError):
            self.apply(payload)
        self.assertEqual(self.stored_files(), stored)

    def test_pending_event_timestamp_outside_saved_transition_is_not_proof(self):
        for when in ('2026-10-04T03:59:59+00:00', '2026-10-04T04:26:38+00:00'):
            with self.subTest(when=when):
                self.model(3)
                self.assertEqual({r['block_id'] for r in self.plan()['rows']}, {'image-1', 'image-2'})
                paths = [self.root / 'review/current.json', *sorted((self.root / 'review/revisions').glob('*.json'))]
                for path in paths:
                    document = json.loads(path.read_text())
                    image = next(b for b in document['blocks'] if b['id'] == 'image-1')
                    if image['review']['status'] == 'needs_review':
                        image['review']['updated_at'] = when
                        path.write_text(json.dumps(document))
                stored = self.stored_files()
                self.assertEqual({r['block_id'] for r in self.plan()['rows']}, {'image-2'})
                self.assertEqual(self.stored_files(), stored)

    def test_missing_or_corrupt_history_cannot_restore_a_candidate(self):
        for mode in ('missing-before-event', 'missing-intermediate', 'corrupt'):
            with self.subTest(mode=mode):
                self.model(3)
                payload = self.payload()
                history = next(p for p in (self.root / 'review/revisions').glob('*.json')
                               if json.loads(p.read_text())['review_session']['revision'] == self.event['review_session']['revision'] - (0 if mode == 'missing-intermediate' else 1))
                if mode == 'corrupt':
                    history.write_text('{invalid json')
                else:
                    history.unlink()
                stored = self.stored_files()
                with self.assertRaises(ValueError):
                    self.apply(payload)
                self.assertEqual(self.stored_files(), stored)
                self.assertEqual(self.plan()['rows'], [])
                # The next synthetic iteration starts from a new valid state;
                # only this fixture's corrupt evidence is removed.
                if mode == 'corrupt':
                    history.unlink()

    def test_alt_caption_or_src_edits_even_if_reverted_are_outside_media_only_proof(self):
        for field, changed in [('alt', 'Different purpose.'), ('caption', 'Changed caption.'), ('src', 'images/changed.png')]:
            with self.subTest(field=field):
                self.model(3)
                original = next(b for b in ensure_review_document(self.root)['blocks'] if b['id'] == 'image-1')[field]
                for value, when in ((changed, '2026-10-04T04:40:00+00:00'), (original, '2026-10-04T04:41:00+00:00')):
                    if field == 'src':
                        document = ensure_review_document(self.root)
                        next(b for b in document['blocks'] if b['id'] == 'image-1')[field] = value
                        with patch('pdf_to_web.review_state.utc_now', return_value=when):
                            save_review_document(self.root, document)
                    else:
                        self.mutate_later('image-1', {field: value}, when=when)
                    self.assertEqual(next(b for b in ensure_review_document(self.root)['blocks'] if b['id'] == 'image-1')[field], value)
                self.assertNotIn('image-1', {r['block_id'] for r in self.plan()['rows']})
                self.assertIn('image-2', {r['block_id'] for r in self.plan()['rows']})

    def test_description_edit_then_revert_is_not_restored(self):
        from pdf_to_web.review_state import update_complex_visual
        self.model(3)
        document = ensure_review_document(self.root)
        visual = next(v for v in document['review']['complex_visuals'] if v['source_block_id'] == 'image-1')
        text = visual['accessibility']['long_description']
        update_complex_visual(self.root, visual['id'], {'long_description': 'A genuine description edit.'})
        update_complex_visual(self.root, visual['id'], {'long_description': text})
        self.assertNotIn('image-1', {r['block_id'] for r in self.plan()['rows']})

    def test_manual_pending_decision_after_media_event_is_not_restored(self):
        self.model(3)
        self.mutate_later('image-1', {'review_status': 'needs_review'})
        self.assertNotIn('image-1', {r['block_id'] for r in self.plan()['rows']})

    def test_manual_pending_decision_in_same_second_as_mapping_is_not_restored(self):
        self.model(3, approve_first=False)
        before = next(b for b in ensure_review_document(self.root)['blocks'] if b['id'] == 'image-1')['review']
        self.assertIn('image-1', {r['block_id'] for r in self.plan()['rows']})
        self.mutate_later('image-1', {'review_status': 'needs_review'}, when=before['updated_at'])
        after = next(b for b in ensure_review_document(self.root)['blocks'] if b['id'] == 'image-1')['review']
        self.assertEqual(after['updated_at'], before['updated_at'])
        self.assertNotEqual(after['decision_id'], before['decision_id'])
        self.assertEqual({r['block_id'] for r in self.plan()['rows']}, {'image-0', 'image-2'})

    def test_pending_description_or_conflicting_association_cannot_be_recovered(self):
        for kind in ('pending-description', 'association-conflict'):
            with self.subTest(kind=kind):
                self.model(3)
                document = ensure_review_document(self.root)
                visual = next(v for v in document['review']['complex_visuals'] if v['source_block_id'] == 'image-1')
                if kind == 'pending-description':
                    visual['status'] = 'needs_text_equivalent'
                else:
                    visual['source_block_id'] = 'image-2'
                save_review_document(self.root, document)
                self.assertNotIn('image-1', {r['block_id'] for r in self.plan()['rows']})

    def test_ambiguous_block_identity_cannot_be_applied(self):
        self.model(3)
        payload = self.payload()
        document = ensure_review_document(self.root)
        document['blocks'].append(copy.deepcopy(document['blocks'][2]))
        save_review_document(self.root, document)
        stored = self.stored_files()
        with self.assertRaises(ValueError):
            self.apply(payload)
        self.assertEqual(self.stored_files(), stored)
