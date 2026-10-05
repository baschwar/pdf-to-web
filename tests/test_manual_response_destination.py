"""Delivery guidance stays with the selected project without moving/importing files."""
import json
import shutil
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

import test_image_draft_routes as fixtures
from fastapi.testclient import TestClient
from pdf_to_web import image_drafts as drafts
from pdf_to_web.review_state import ensure_review_document
from pdf_to_web.web import WebAppConfig, create_app


class PromptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.prompt = ''

    def handle_starttag(self, tag, attrs):
        if dict(attrs).get('id') == 'draft-copy-instructions-text':
            self.inside = True

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.inside = False

    def handle_data(self, text):
        if self.inside:
            self.prompt += text


class ManualResponseDestinationTests(unittest.TestCase):
    setUp = fixtures.ImageDraftRouteTests.setUp
    post = fixtures.ImageDraftRouteTests.post

    def selected_prompt(self):
        parser = PromptParser()
        response = self.client.get('/structure')
        self.assertEqual(response.status_code, 200)
        parser.feed(response.text)
        return parser.prompt

    def select(self, root):
        with mock.patch('pdf_to_web.web.choose_project_folder', return_value=root):
            token = self.client.post('/api/picker/project', headers=self.headers, json={}).json()['selection']['token']
        result = self.client.post('/api/projects/open', headers=self.headers, json={'selection_token': token})
        self.assertEqual(result.status_code, 200, result.text)
        self.root = root
        self.document_id = ensure_review_document(root)['output_pages']['project_id']

    def test_project_prompt_discloses_real_destination_without_writing_or_approving(self):
        path = self.root / 'review/current.json'
        before = path.read_bytes()
        prompt = self.selected_prompt()
        self.assertIn(str(self.root.resolve() / 'output/image-drafts'), prompt)
        self.assertIn('authorized local filesystem access', prompt)
        self.assertIn('Do not invent another folder', prompt)
        self.assertIn('attachment/download', prompt)
        self.assertEqual(prompt, drafts.manual_exchange_prompt(self.root))
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse(list((self.root / 'output/image-drafts').glob('*.json')))

    def test_export_prompt_package_and_metadata_use_same_unique_response_path(self):
        result = self.post('export', {'block_ids': ['photo']})
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()
        with zipfile.ZipFile(data['saved_path']) as archive:
            request = json.loads(archive.read('request.json'))
            self.assertEqual(data['response_delivery'], request['response_delivery'])
            self.assertEqual(data['manual_instructions'], archive.read('INSTRUCTIONS.txt').decode('utf-8'))
            self.assertEqual(data['manual_instructions'], request['instructions'])
        destination = Path(data['response_delivery']['suggested_path'])
        self.assertEqual(destination.parent, self.root.resolve() / 'output/image-drafts')
        self.assertIn('image-draft-response-', destination.name)
        self.assertEqual(destination.suffix, '.json')
        self.assertIn(str(destination), data['manual_instructions'])
        self.assertFalse(destination.exists())
        second = self.post('export', {'block_ids': ['photo']}).json()
        self.assertNotEqual(destination, Path(second['response_delivery']['suggested_path']))

    def test_chosen_folders_spaces_unicode_and_project_switch_update_every_destination(self):
        old = self.root
        chosen = old.parent / 'Synthetic folder α 日本語 & spaces'
        shutil.copytree(old, chosen)
        self.select(chosen)
        prompt = self.selected_prompt()
        self.assertIn(str(chosen.resolve() / 'output/image-drafts'), prompt)
        self.assertNotIn(str(old.resolve() / 'output/image-drafts'), prompt)
        data = self.post('export', {'block_ids': ['photo']}).json()
        self.assertEqual(data['response_delivery']['directory'], str(chosen.resolve() / 'output/image-drafts'))
        self.assertIn(str(chosen.resolve()), data['manual_instructions'])
        self.select(old)
        prompt = self.selected_prompt()
        self.assertIn(str(old.resolve() / 'output/image-drafts'), prompt)
        self.assertNotIn(str(chosen), prompt)

    def test_existing_responses_are_never_replaced_and_collision_rule_is_explicit(self):
        directory = self.root / 'output/image-drafts'
        directory.mkdir(exist_ok=True)
        package = directory / 'fixture-image-drafting-request-unique.zip'
        first = Path(drafts.manual_response_delivery(self.root, package)['suggested_path'])
        first.write_text('previous response')
        second = first.with_name(first.stem + '-2.json')
        second.write_text('another response')
        delivery = drafts.manual_response_delivery(self.root, package)
        self.assertEqual(Path(delivery['suggested_path']).name, first.stem + '-3.json')
        self.assertEqual(first.read_text(), 'previous response')
        self.assertEqual(second.read_text(), 'another response')
        self.assertIn('Never overwrite', delivery['collision_policy'])
        self.assertIn('next unused number', drafts.manual_exchange_prompt(self.root, delivery))

    def test_response_filename_changes_preserve_existing_import_identity_and_schema(self):
        data = self.post('export', {'block_ids': ['photo']}).json()
        with zipfile.ZipFile(data['saved_path']) as archive:
            payload = json.loads(archive.read('response-template.json'))
        payload['responses'][0]['alt'] = 'Synthetic fixture image in context'
        response = Path(data['response_delivery']['suggested_path']).with_name('Renamed response α & spaces.json')
        response.write_text(json.dumps(payload))
        before = (self.root / 'review/current.json').read_bytes()
        validated = self.post('import', {'response': json.loads(response.read_text())})
        self.assertEqual(validated.json()['valid_count'], 1)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        blocks = ensure_review_document(self.root)['blocks']
        imported = self.post('import', {'response': payload, 'commit': True})
        self.assertEqual(imported.json()['valid_count'], 1)
        self.assertEqual(ensure_review_document(self.root)['blocks'], blocks)

    def test_no_active_project_has_no_invented_local_destination(self):
        prompt = drafts.manual_exchange_prompt()
        self.assertIn('No project destination is available', prompt)
        self.assertIn('attachment/download', prompt)
        config = WebAppConfig(projects_root=self.root.parent, recent_store=self.root.parent / 'no-project-recent.json', port=54321, bootstrap_token='bootstrap', session_token='session', csrf_token='csrf')
        with TestClient(create_app(config), base_url='http://127.0.0.1:54321') as client:
            client.get('/bootstrap/bootstrap')
            result = client.post('/api/image-drafts/export', headers=self.headers, json={'block_ids': ['photo']})
            self.assertEqual(result.status_code, 400)
            self.assertEqual(result.json()['detail'], 'Choose a project first')


if __name__ == '__main__':
    unittest.main()
