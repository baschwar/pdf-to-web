"""Help is available before project selection and never changes review data."""
import re
import unittest

from fastapi.testclient import TestClient
import test_image_draft_routes as fixtures
from pdf_to_web.web import WebAppConfig, create_app


class WorkflowHelpTests(unittest.TestCase):
    setUp = fixtures.ImageDraftRouteTests.setUp

    def test_contextual_help_targets_resolve_without_changing_saved_review(self):
        paths = [self.root / 'project.json', self.root / 'review/current.json',
                 *sorted((self.root / 'review/revisions').glob('*.json'))]
        before = {path: path.read_bytes() for path in paths}
        help_page = self.client.get('/help')
        self.assertEqual(help_page.status_code, 200)
        ids = set(re.findall(r'\bid="([^"]+)"', help_page.text))
        for route in ('/', '/structure', '/accessibility', '/output-pages', '/export'):
            page = self.client.get(route)
            self.assertEqual(page.status_code, 200)
            for target in re.findall(r'href="/help#([^"]+)"', page.text):
                self.assertIn(target, ids, (route, target))
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.client.cookies.clear()
        self.assertEqual(self.client.get('/help').status_code, 401)

    def test_help_available_without_project_workflow_remains_unavailable(self):
        config = WebAppConfig(port=54322, recent_store=self.root / 'help-recent.json',
                              projects_root=self.root / 'help-projects', bootstrap_token='help-bootstrap')
        with TestClient(create_app(config), base_url='http://127.0.0.1:54322') as client:
            client.get('/bootstrap/help-bootstrap')
            page = client.get('/help')
            self.assertEqual(page.status_code, 200)
            self.assertIn('href="/help" aria-current="page"', page.text)
            self.assertIn('<span aria-disabled="true">Structure</span>', page.text)
            self.assertEqual(client.get('/api/document').status_code, 400)
            self.assertFalse(config.projects_root.exists())
