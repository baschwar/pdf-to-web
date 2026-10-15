"""Help is available before project selection and never changes review data."""
import re
import unittest
from html.parser import HTMLParser

from fastapi.testclient import TestClient
import test_image_draft_routes as fixtures
from pdf_to_web.web import WebAppConfig, create_app


class FooterLinks(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.in_footer = False
        self.current = None
        self.links = []
        self.feed(page)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == 'footer' and 'app-footer' in attributes.get('class', '').split():
            self.in_footer = True
        elif self.in_footer and tag == 'a':
            self.current = {'attributes': attributes, 'text': ''}
            self.links.append(self.current)

    def handle_endtag(self, tag):
        if tag == 'footer':
            self.in_footer = False
        elif tag == 'a':
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data


class WorkflowHelpTests(unittest.TestCase):
    setUp = fixtures.ImageDraftRouteTests.setUp

    def assert_documentation_footer(self, page):
        links = {' '.join(link['text'].split()): link['attributes']
                 for link in FooterLinks(page).links}
        self.assertEqual(len(links), 3)
        for label, filename in [('README', 'README.md'), ('Changelog', 'CHANGELOG.md')]:
            attributes = links[label + ' (opens a new tab)']
            self.assertEqual(attributes['href'],
                             'https://github.com/baschwar/pdf-to-web/blob/main/' + filename)
            self.assertEqual(attributes['target'], '_blank')
            self.assertTrue({'noopener', 'noreferrer'} <= set(attributes['rel'].split()))
        self.assertEqual(links['Accessibility review limits']['href'], '/help#acceptance')

    def test_documentation_footer_on_all_workflow_pages_preserves_saved_review(self):
        paths = [self.root / 'project.json', self.root / 'review/current.json',
                 *sorted((self.root / 'review/revisions').glob('*.json'))]
        before = {path: path.read_bytes() for path in paths}
        for route in ('/', '/document', '/structure', '/accessibility',
                      '/output-pages', '/preview', '/export', '/help'):
            with self.subTest(route=route):
                page = self.client.get(route)
                self.assertEqual(page.status_code, 200)
                self.assert_documentation_footer(page.text)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

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
            self.assert_documentation_footer(page.text)
            self.assert_documentation_footer(client.get('/').text)
            self.assertEqual(client.get('/api/document').status_code, 400)
            self.assertFalse(config.projects_root.exists())
