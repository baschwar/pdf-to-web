"""Draft completion controls disclosure defaults without changing reviewed content."""
import copy
import re
import unittest
import test_image_draft_routes as routes
from pdf_to_web import image_drafts as drafts
from pdf_to_web.image_draft_ui import workflow_state
from pdf_to_web.review_state import ensure_review_document, save_review_document


class DraftingCollapseTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp
    post = routes.ImageDraftRouteTests.post

    def tag(self):
        return re.search(r'<details id="image-description-tools"[^>]*>', self.client.get('/structure').text).group()

    def test_successful_manual_import_collapses_next_visit_without_approval(self):
        self.assertIn(' open', self.tag())
        entry = drafts.prepare(self.root, ['photo'])[0]
        response = self.fixture.response(entry)
        self.assertTrue(workflow_state(ensure_review_document(self.root), 1)['open'])
        blocks = copy.deepcopy(ensure_review_document(self.root)['blocks'])
        drafts.import_response(self.root, response, commit=True)
        before = (self.root / 'review/current.json').read_bytes()
        self.assertNotIn(' open', self.tag())
        self.assertIn('data-generation-completed="true"', self.tag())
        self.assertIn('drafts ready — review image blocks', self.client.get('/structure').text)
        after = ensure_review_document(self.root)['blocks']
        self.assertEqual([b['id'] for b in after], [b['id'] for b in blocks])
        photo = next(b for b in after if b['id'] == 'photo')
        self.assertEqual(photo['alt'], 'Accepted ALT')
        self.assertEqual(photo['caption'], 'Accepted CAPTION')
        self.assertEqual(photo['review']['status'], 'needs_review')
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_completed_history_survives_superseded_request_and_failed_retry_is_visible(self):
        entry = drafts.prepare(self.root, ['photo'])[0]
        drafts.import_response(self.root, self.fixture.response(entry), commit=True)
        new = drafts.prepare(self.root, ['photo'], regenerate=True)[0]
        self.assertNotIn(' open', self.tag())
        doc = ensure_review_document(self.root)
        doc['image_description_drafts']['requests'][new['request_id']].update(status='failed', error='Fixture failure')
        save_review_document(self.root, doc)
        before = (self.root / 'review/current.json').read_bytes()
        self.assertIn(' open', self.tag())
        screen = self.client.get('/structure').text
        self.assertLess(screen.index('failed — retry or inspect the error'), screen.index('id="image-description-tools"'))
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_defaults_are_read_only_and_old_ready_rejected_or_retained_drafts_count_as_success(self):
        for entry in ({'status':'ready'}, {'status':'rejected'}, {'status':'cancelled','draft':{'alt':'Retained'}}):
            with self.subTest(entry=entry):
                doc={'image_description_drafts':{'requests':{'old':entry},'active':{}}}
                before=copy.deepcopy(doc)
                self.assertFalse(workflow_state(doc, 54)['open'])
                self.assertTrue(workflow_state(doc, 54)['completed'])
                self.assertEqual(doc,before)
        self.assertTrue(workflow_state({},1)['open'])
        self.assertFalse(workflow_state({},0)['open'])
        doc={'image_description_drafts':{'requests':{'new':{'status':'generating'}},'active':{'photo':'new'}}}
        self.assertTrue(workflow_state(doc,0)['open'])
        self.assertIn('generating',workflow_state(doc,0)['status'])
