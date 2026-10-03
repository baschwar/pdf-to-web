"""Drafting entry points and project-local request ZIP persistence."""
import json
import re
import shutil
import unittest
import zipfile
from pathlib import Path
from unittest import mock
from fastapi.testclient import TestClient

import test_image_draft_routes as routes
from pdf_to_web import image_drafts as drafts
from pdf_to_web.review_state import ensure_review_document
from pdf_to_web.web import WebAppConfig, create_app


class DraftingDiscoveryTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp
    post = routes.ImageDraftRouteTests.post

    def test_section_is_distinct_collapsed_and_findings_link_to_existing_tools(self):
        screen = self.client.get('/structure').text
        self.assertIn('class="image-draft-workflow" aria-labelledby="image-draft-heading"', screen)
        self.assertEqual(screen.count('id="image-draft-heading"'), 1)
        self.assertIn('<h2 id="image-draft-heading" tabindex="-1">Image description drafts</h2>', screen)
        tag = re.search(r'<details id="image-description-tools"[^>]*>', screen).group()
        self.assertNotIn(' open', tag)
        self.assertIn('href="#image-description-tools" class="draft-workflow-link"', screen)
        finding = self.client.get('/accessibility').text.split('id="finding-image-alt:ambiguous"')[1].split('</article>')[0]
        self.assertIn('href="/structure#image-description-tools"', finding)
        self.assertIn('Draft image descriptions', finding)
        before = (self.root / 'review/current.json').read_bytes()
        self.client.get('/structure#image-description-tools')
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_blocked_and_imageless_projects_do_not_offer_missing_tools(self):
        from pdf_to_web.review_state import save_review_document
        document = ensure_review_document(self.root)
        document['review']['status'] = 'conversion_blocked'
        save_review_document(self.root, document)
        for route in ('/structure', '/accessibility'):
            self.assertNotIn('class="draft-workflow-link"', self.client.get(route).text)
        document['review']['status'] = 'needs_review'
        document['blocks'] = [b for b in document['blocks'] if b['type'] != 'image']
        save_review_document(self.root, document)
        self.assertNotIn('id="image-description-tools"', self.client.get('/structure').text)

    def test_repeated_packages_remain_in_chosen_root_and_download_after_reopen(self):
        chosen = self.root.parent / 'Chosen folder α'
        shutil.copytree(self.root, chosen)
        with mock.patch('pdf_to_web.web.choose_project_folder', return_value=chosen):
            selected = self.client.post('/api/picker/project', headers=self.headers, json={}).json()['selection']
        response = self.client.post('/api/projects/open', headers=self.headers, json={'selection_token': selected['token']})
        self.assertEqual(response.status_code, 200, response.text)
        self.root = chosen
        before = ensure_review_document(chosen)['blocks']
        first = self.post('export', {'block_ids': ['photo']}).json()
        second = self.post('export', {'block_ids': ['photo']}).json()
        self.assertNotEqual(first['filename'], second['filename'])
        self.assertRegex(first['filename'], r'^draft-fixture-image-drafting-request-\d{8}T\d+Z-[a-f0-9]+\.zip$')
        for result in (first, second):
            package = Path(result['saved_path'])
            self.assertEqual(package.parent, chosen.resolve() / 'output/image-drafts')
            self.assertEqual(package, chosen.resolve() / result['relative_path'])
            self.assertEqual(self.client.get(result['url']).content, package.read_bytes())
            with zipfile.ZipFile(package) as archive:
                request = json.loads(archive.read('request.json'))['requests'][0]
                answer = json.loads(archive.read('response-template.json'))['responses'][0]
                self.assertEqual({k: request[k] for k in drafts.IDENTITY}, {k: answer[k] for k in drafts.IDENTITY})
                self.assertIn('nothing is approved automatically', archive.read('INSTRUCTIONS.txt').decode())
        self.assertEqual(ensure_review_document(chosen)['blocks'], before)
        config = WebAppConfig(project=chosen, recent_store=chosen/'reopen-recent.json', port=54321,
                              bootstrap_token='bootstrap', session_token='session', csrf_token='csrf')
        with TestClient(create_app(config), base_url='http://127.0.0.1:54321') as client:
            client.get('/bootstrap/bootstrap')
            self.assertEqual(client.get(first['url']).content, Path(first['saved_path']).read_bytes())
        self.assertFalse(list((chosen / 'output/image-drafts').glob('*.tmp')))

    def test_failed_zip_write_preserves_earlier_package_and_cleans_incomplete_file(self):
        entry = drafts.prepare(self.root, ['photo'])[0]
        package = drafts.exchange_package(self.root, [entry])
        original = package.read_bytes()
        with mock.patch('zipfile.ZipFile.writestr', side_effect=OSError('Synthetic disk write failure')):
            response = self.post('export', {'block_ids': ['photo']})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Could not save drafting request ZIP', response.json()['error'])
        self.assertEqual(package.read_bytes(), original)
        self.assertEqual(list(package.parent.iterdir()), [package])

    def test_output_symlink_cannot_write_outside_project(self):
        outside = self.root.parent / 'outside-output'
        outside.mkdir()
        (self.root / 'output/image-drafts').symlink_to(outside, target_is_directory=True)
        response = self.post('export', {'block_ids': ['photo']})
        self.assertEqual(response.status_code, 400)
        self.assertIn('stay inside this project', response.json()['error'])
        self.assertEqual(list(outside.iterdir()), [])
