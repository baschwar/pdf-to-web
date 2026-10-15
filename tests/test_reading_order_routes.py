"""Authenticated reading-order endpoints retain exact saved scope."""
import unittest
from fastapi.testclient import TestClient
import test_reading_order as fixture
from pdf_to_web.web import WebAppConfig, create_app
from pdf_to_web.review_state import review_path, ensure_review_document

class ReadingOrderRouteTests(unittest.TestCase):
    def setUp(self):
        fixture.ReadingOrderTests.setUp(self)
        config=WebAppConfig(project=self.root,port=54321,bootstrap_token='bootstrap',session_token='session',csrf_token='csrf',recent_store=self.root/'recent.json')
        self.client=TestClient(create_app(config),base_url='http://127.0.0.1:54321');self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)
        self.headers={'Origin':'http://127.0.0.1:54321','x-csrf-token':'csrf'}

    def test_authentication_and_csrf_are_required_and_snapshot_does_not_write(self):
        before=review_path(self.root).read_bytes()
        self.assertEqual(self.client.get('/api/source-pages/1/reading-order').status_code,401)
        self.client.get('/bootstrap/bootstrap')
        response=self.client.get('/api/source-pages/1/reading-order');self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.post('/api/source-pages/1/reading-order',json={}).status_code,403)
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_route_apply_and_repeated_old_snapshot_cannot_add_second_write(self):
        self.client.get('/bootstrap/bootstrap');snapshot=self.client.get('/api/source-pages/1/reading-order').json()
        body={'block_ids':['a','d','b','geometryless'],'project_id':snapshot['project_id'],'expected_review_token':snapshot['review_token']}
        result=self.client.post('/api/source-pages/1/reading-order',headers=self.headers,json=body);self.assertEqual(result.status_code,200,result.text)
        before=review_path(self.root).read_bytes();history=list((self.root/'review/revisions').glob('*.json'))
        result=self.client.post('/api/source-pages/1/reading-order',headers=self.headers,json=body);self.assertEqual(result.status_code,400)
        self.assertIn('project changed',result.json()['error'])
        self.assertEqual(review_path(self.root).read_bytes(),before);self.assertEqual(list((self.root/'review/revisions').glob('*.json')),history)
        self.assertEqual(ensure_review_document(self.root)['blocks'][2]['id'],'d')

    def test_structure_exposes_only_local_assets_and_clear_document_move_labels(self):
        self.client.get('/bootstrap/bootstrap');page=self.client.get('/structure').text
        self.assertIn('Repair reading order on this page',page)
        self.assertIn('Move to document start',page)
        self.assertIn('/static/reading-order.bundle.js',page)
        self.assertIn('/static/reading-order.css',page)
        self.assertIn('aria-label="Source page"',page)
        self.assertIn('<span aria-hidden="true">ⓘ</span>',page)
        bundle=self.client.get('/static/reading-order.bundle.js');self.assertEqual(bundle.status_code,200)

    def test_staged_preview_requires_auth_csrf_and_never_writes(self):
        self.client.get('/bootstrap/bootstrap');snapshot=self.client.get('/api/source-pages/1/reading-order').json()
        body={'project_id':snapshot['project_id'],'expected_review_token':snapshot['review_token'],
              'operations':[{'action':'order','block_ids':['a','d','b','geometryless']}]}
        before=review_path(self.root).read_bytes()
        self.assertEqual(self.client.post('/api/source-pages/1/reading-order/preview',json=body).status_code,403)
        response=self.client.post('/api/source-pages/1/reading-order/preview',headers=self.headers,json=body)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['transaction_version'],1)
        self.assertEqual(review_path(self.root).read_bytes(),before)
