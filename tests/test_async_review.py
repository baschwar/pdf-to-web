"""Confirmed saves return bounded review fragments; refresh failure is not a failed write."""
import unittest
from unittest import mock
import test_image_draft_routes as fixtures
from pdf_to_web.review_state import ensure_review_document
from pdf_to_web.image_review import review_token


class AsyncReviewTests(unittest.TestCase):
    setUp = fixtures.ImageDraftRouteTests.setUp

    def post(self, path, data):
        return self.client.post(path, headers=self.headers, json=data)

    def test_save_and_approve_returns_only_changed_card_with_current_tokens(self):
        token = review_token(ensure_review_document(self.root))
        result = self.post('/api/blocks/p/save-and-approve', {'content':'Updated verified context','expected_review_token':token,'review_refresh':True})
        self.assertEqual(result.status_code,200,result.text)
        data = result.json();patch = data['review_patch']
        self.assertIn('1', patch['source_page_reviews'])
        self.assertIn(patch['source_page_reviews']['1']['state'], {'needs', 'partial', 'reviewed'})
        self.assertEqual(len(patch['cards']),1)
        self.assertIn('id="block-p"',patch['cards'][0])
        self.assertIn('Updated verified context',patch['cards'][0])
        self.assertEqual(patch['review_token'],review_token(ensure_review_document(self.root)))
        self.assertIn(patch['review_token'],patch['cards'][0])
        self.assertTrue(patch['can_undo'])
        self.assertNotIn('<html',patch['cards'][0])
        self.assertEqual(self.client.get('/structure').headers['cache-control'],'private, no-store')

    def test_bare_approval_revalidates_snapshot_before_committing(self):
        token = review_token(ensure_review_document(self.root))
        self.post('/api/blocks/p',{'content':'Newer text'})
        before=(self.root/'review/current.json').read_bytes()
        result=self.post('/api/blocks/p/approve',{'expected_review_token':token,'review_refresh':True})
        self.assertEqual(result.status_code,400)
        self.assertEqual((self.root/'review/current.json').read_bytes(),before)

    def test_refresh_failure_reports_confirmed_save_without_repeating_it(self):
        before=ensure_review_document(self.root)['review_session']['revision']
        with mock.patch('pdf_to_web.web._structure_review_patch',side_effect=RuntimeError('display unavailable')):
            result=self.post('/api/blocks/p',{'content':'Saved once','review_refresh':True})
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['status'],'ok')
        self.assertIn('Saved, but',result.json()['refresh_error'])
        document=ensure_review_document(self.root)
        self.assertEqual(document['review_session']['revision'],before+1)
        self.assertEqual(next(b for b in document['blocks'] if b['id']=='p')['content'],'Saved once')


if __name__=='__main__':
    unittest.main()
