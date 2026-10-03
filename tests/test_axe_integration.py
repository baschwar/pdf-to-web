import unittest
from copy import deepcopy
import test_image_draft_routes as routes
from pdf_to_web.exporters.html import render_document
from pdf_to_web.review_state import ensure_review_document, save_review_document


class AxeIntegrationTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def test_accessibility_loads_local_scan_automatically(self):
        page = self.client.get('/accessibility').text
        self.assertIn('/static/accessibility-scan.js', page)
        self.assertIn('src="/api/accessibility/preview"', page)
        self.assertIn('Checking rendered HTML', page)
        self.assertNotIn('Generate accessibility report', page)
        self.assertNotIn('/static/accessibility-scan.js', self.client.get('/structure').text)
        self.assertEqual(self.client.get('/static/axe.min.js').status_code, 200)

    def test_audit_projection_preserves_state_and_blocks_external_requests(self):
        before = ensure_review_document(self.root)
        response = self.client.get('/api/accessibility/preview')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-pdf-block-id="photo"', response.text)
        self.assertIn('/static/axe.min.js', response.text)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        policy = response.headers['content-security-policy']
        self.assertIn("default-src 'none'", policy)
        self.assertIn("img-src 'self' data:", policy)
        self.assertNotIn('https:', policy)
        self.assertEqual(ensure_review_document(self.root), before)
        self.client.cookies.clear()
        self.assertEqual(self.client.get('/api/accessibility/preview').status_code, 401)

    def test_annotations_are_opt_in_escaped_and_exclusions_stay_excluded(self):
        document = {'metadata': {'title': 'Test'}, 'blocks': [
            {'id': 'a"<', 'type': 'paragraph', 'content': '<script>bad()</script>'},
            {'id': 'excluded', 'type': 'paragraph', 'content': 'Secret', 'review': {'status': 'excluded'}},
        ]}
        original = deepcopy(document)
        annotated = render_document(document, annotate_blocks=True)
        self.assertIn('data-pdf-block-id="a&quot;&lt;"', annotated)
        self.assertNotIn('<script>', annotated)
        self.assertNotIn('Secret', annotated)
        self.assertNotIn('data-pdf-block-id', render_document(document))
        self.assertEqual(document, original)
