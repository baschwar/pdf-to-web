import json
import io
import zipfile
import threading
import time
import unittest
from unittest import mock
import test_image_drafts as fixtures
from fastapi.testclient import TestClient
from pdf_to_web.web import WebAppConfig, create_app
from pdf_to_web import image_drafts as d
from pdf_to_web.review_state import ensure_review_document
from pdf_to_web.image_draft_ui import MANUAL_EXCHANGE_PROMPT


class ImageDraftRouteTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.ImageDraftTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.root = fixture.root
        self.config = WebAppConfig(project=self.root, recent_store=self.root / 'recent.json', port=54321, bootstrap_token='bootstrap', session_token='session', csrf_token='csrf')
        self.client = TestClient(create_app(self.config), base_url='http://127.0.0.1:54321')
        self.client.__enter__(); self.addCleanup(self.client.__exit__, None, None, None)
        self.client.get('/bootstrap/bootstrap')
        self.headers = {'Origin': 'http://127.0.0.1:54321', 'x-csrf-token': 'csrf'}
        self.document_id = ensure_review_document(self.root)['output_pages']['project_id']

    def post(self, action, data):
        return self.client.post('/api/image-drafts/' + action, headers=self.headers, json={'document_id': self.document_id, **data})

    def wait_status(self, target):
        for i in range(100):
            entries = self.client.get('/api/image-drafts').json()['entries']
            if entries and entries[0]['status'] == target: return entries[0]
            time.sleep(.01)
        self.fail(f'Expected {target}, received {entries}')

    def test_session_csrf_identity_and_asset_confinement(self):
        self.assertEqual(self.client.post('/api/image-drafts/export', json={}).status_code, 403)
        self.assertEqual(self.post('export', {'document_id': 'other', 'block_ids': ['photo']}).status_code, 400)
        self.assertEqual(self.client.get('/api/image-drafts/asset', params={'path': '../project.json'}).status_code, 404)
        self.assertEqual(self.client.get('/api/image-drafts/asset', params={'path': 'extraction/raw/images/photo.png'}).status_code, 200)
        self.client.cookies.clear()
        self.assertEqual(self.client.get('/api/image-drafts').status_code, 401)

    def test_manual_exchange_needs_no_ollama_even_with_saved_local_provider_or_blank_model(self):
        self.assertEqual(self.post('settings', {'provider': 'ollama-local', 'model': 'offline-fixture-model'}).status_code, 200)
        with mock.patch.object(d, 'OllamaProvider', side_effect=AssertionError('Manual exchange must never initialize Ollama')):
            exported = self.post('export', {'block_ids': ['photo']})
            self.assertEqual(exported.status_code, 200, exported.text)
            entry = next(iter(d.state(ensure_review_document(self.root))['requests'].values()))
            self.assertEqual(entry['provider'], 'manual')
            self.assertEqual(entry['model'], 'manual')
            self.assertEqual(self.post('import', {'response': self.fixture.response(entry)}).json()['valid_count'], 1)
            self.assertEqual(self.post('settings', {'provider': 'manual', 'model': ''}).status_code, 200)
            screen = self.client.get('/structure').text
            self.assertIn('id="draft-model-label" hidden', screen)
            self.assertIn('id="draft-provider-route" hidden', screen)
            self.assertNotIn('id="draft-model" name="model" required', screen)
            self.assertEqual(self.post('export', {'block_ids': ['photo']}).status_code, 200)

    def test_manual_export_preview_import_and_apply(self):
        result = self.post('export', {'block_ids': ['photo']})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(self.client.get(result.json()['url']).status_code, 200)
        entry = d.state(ensure_review_document(self.root))['requests'].values().__iter__().__next__()
        response = self.fixture.response(entry)
        result = self.post('import', {'response': response})
        self.assertEqual(result.json()['valid_count'], 1)
        self.assertIsNone(d.state(ensure_review_document(self.root))['requests'][entry['request_id']]['draft'])
        self.post('import', {'response': response, 'commit': True})
        result = self.post('apply', {'block_id': 'photo', 'request_id': entry['request_id'], 'fields': ['alt']})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(d.image(ensure_review_document(self.root), 'photo')['alt'], 'DRAFT ALT')
        self.assertIn('Draft alt text', self.client.get('/structure').text)

    def test_copy_instructions_agree_with_actual_zip_and_identity_schema(self):
        response = self.post('export', {'block_ids': ['photo']})
        self.assertEqual(response.status_code, 200, response.text)
        downloaded = self.client.get(response.json()['url'])
        with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
            for filename in ('INSTRUCTIONS.txt', 'request.json', 'response-template.json', 'review-sheet.csv'):
                self.assertIn(filename, archive.namelist())
                self.assertIn(filename, MANUAL_EXCHANGE_PROMPT)
            request = json.loads(archive.read('request.json'))
            template = json.loads(archive.read('response-template.json'))
            self.assertEqual(template['schema_version'], d.EXCHANGE)
            self.assertIn(d.EXCHANGE, MANUAL_EXCHANGE_PROMPT)
            self.assertEqual(len(request['requests']), len(template['responses']))
            for source, reply in zip(request['requests'], template['responses']):
                self.assertIn(source['image_file'], archive.namelist())
                for key in d.IDENTITY:
                    self.assertIn(key, MANUAL_EXCHANGE_PROMPT)
                    self.assertEqual(reply[key], source[key])
                self.assertIsNone(reply['caption'])
                self.assertIsNone(reply['long_description'])
        self.assertIn('captions only when warranted (otherwise null)', MANUAL_EXCHANGE_PROMPT)
        self.assertIn('nothing is automatically approved', MANUAL_EXCHANGE_PROMPT)

    def test_blank_export_template_rejects_without_save_and_completed_copy_validates_then_imports(self):
        exported = self.post('export', {'block_ids': ['photo']}).json()
        with zipfile.ZipFile(io.BytesIO(self.client.get(exported['url']).content)) as archive:
            payload = json.loads(archive.read('response-template.json'))
            self.assertIn('template.json is blank', archive.read('INSTRUCTIONS.txt').decode())
        saved = (self.root / 'review/current.json').read_bytes()
        rejected = self.post('import', {'response': payload}).json()
        self.assertEqual(rejected['valid_count'], 0)
        self.assertIn('Invalid alt:', rejected['findings'][0]['error'])
        self.assertEqual((self.root / 'review/current.json').read_bytes(), saved)
        payload['responses'][0]['alt'] = 'A meaningful synthetic description for review.'
        accepted = self.post('import', {'response': payload}).json()
        self.assertEqual(accepted['valid_count'], 1)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), saved)
        original_blocks = ensure_review_document(self.root)['blocks']
        committed = self.post('import', {'response': payload, 'commit': True}).json()
        self.assertEqual(committed['valid_count'], 1)
        document = ensure_review_document(self.root)
        self.assertEqual(document['blocks'], original_blocks)
        entry = d.state(document)['requests'][payload['responses'][0]['request_id']]
        self.assertEqual(entry['draft']['alt'], payload['responses'][0]['alt'])
        self.assertIsNone(entry['draft']['caption'])
        self.assertIsNone(entry['draft']['long_description'])

    def test_copy_instructions_controls_render_read_only_without_changing_saved_state(self):
        from html.parser import HTMLParser
        class Controls(HTMLParser):
            def __init__(self):
                super().__init__(); self.fields = {}; self.text = ''; self.in_prompt = False
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if values.get('id'): self.fields[values['id']] = (tag, values)
                if values.get('id') == 'draft-copy-instructions-text': self.in_prompt = True
            def handle_data(self, text):
                if self.in_prompt: self.text += text
            def handle_endtag(self, tag):
                if tag == 'textarea': self.in_prompt = False
        ensure_review_document(self.root)
        paths = [self.root / 'review/current.json', self.root / 'project.json',
                 *sorted((self.root / 'review/revisions').glob('*.json'))]
        saved = {p: p.read_bytes() for p in paths}
        page = self.client.get('/structure')
        self.assertEqual(page.status_code, 200, page.text)
        parsed = Controls(); parsed.feed(page.text)
        self.assertEqual(parsed.text, d.manual_exchange_prompt(self.root))
        _, button = parsed.fields['draft-copy-instructions']
        self.assertEqual(button['type'], 'button')
        self.assertEqual(button['aria-describedby'], 'draft-manual-flow')
        _, text = parsed.fields['draft-copy-instructions-text']
        self.assertIn('readonly', text); self.assertIn('hidden', text)
        _, status = parsed.fields['draft-copy-instructions-status']
        self.assertEqual(status['role'], 'status')
        self.assertEqual({p: p.read_bytes() for p in paths}, saved)

    def test_mock_generation_failure_then_retry_and_success_cache(self):
        options = {'block_ids': ['photo'], 'provider': 'ollama-local', 'model': 'mock'}
        with mock.patch.object(d.OllamaProvider, 'generate', side_effect=RuntimeError('SECRET do not persist')):
            self.assertEqual(self.post('generate', options).status_code, 200)
            self.wait_status('failed')
        self.assertNotIn('SECRET', json.dumps(d.state(ensure_review_document(self.root))))
        def generate(provider, entry, path): return self.fixture.response(entry)['responses'][0]
        with mock.patch.object(d.OllamaProvider, 'generate', generate):
            self.post('generate', options)
            done = self.wait_status('ready')
            self.post('generate', options)
            self.assertEqual(self.wait_status('ready')['request_id'], done['request_id'])
        self.assertEqual(d.image(ensure_review_document(self.root), 'photo')['alt'], 'Accepted ALT')

    def test_cloud_requires_specific_preflight_consent_without_using_existing_keys(self):
        options = {'block_ids': ['photo'], 'provider': 'openai'}
        with mock.patch.dict('os.environ', {'PDF_TO_WEB_OPENAI_API_KEY': 'fixture-key'}), mock.patch.object(d.OpenAIProvider, 'generate', side_effect=RuntimeError('mock only')) as generate:
            self.assertEqual(self.post('generate', options).status_code, 400)
            generate.assert_not_called()
            preview = self.post('preflight', options).json()
            self.assertIn('current_alt', preview['requests'][0]['context'])
            denied = self.post('generate', options | {'authorize_cloud': True, 'consent_hash': 'wrong'})
            self.assertEqual(denied.status_code, 400)
            self.assertEqual(self.post('generate', options | {'authorize_cloud': True, 'consent_hash': preview['consent_hash']}).status_code, 200)
            self.wait_status('failed')
            self.assertNotIn('fixture-key', json.dumps(d.state(ensure_review_document(self.root))))

    def test_late_response_after_cancellation(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def generate(provider, entry, path):
            entered.set(); release.wait(3)
            return self.fixture.response(entry)['responses'][0]
        with mock.patch.object(d.OllamaProvider, 'generate', generate):
            self.post('generate', {'block_ids': ['photo'], 'model': 'mock'})
            self.assertTrue(entered.wait(1))
            entry = self.wait_status('generating')
            self.post('cancel', entry)
            release.set()
            self.wait_status('cancelled')
            self.assertEqual(d.image(ensure_review_document(self.root), 'photo')['alt'], 'Accepted ALT')

    def test_project_switch_cancels_old_generation_and_rejects_old_ui(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def generate(provider, entry, path):
            entered.set(); release.wait(3)
            return self.fixture.response(entry)['responses'][0]
        with mock.patch.object(d.OllamaProvider, 'generate', generate):
            self.post('generate', {'block_ids': ['photo'], 'model': 'mock'})
            self.assertTrue(entered.wait(1))
            # Reopening the current project is also a switch; the old job epoch is cancelled.
            with mock.patch('pdf_to_web.web.choose_project_folder', return_value=self.root):
                picked = self.client.post('/api/picker/project', headers=self.headers, json={}).json()
            self.client.post('/api/projects/open', headers=self.headers, json={'selection_token': picked['selection']['token']})
            release.set()
            self.wait_status('cancelled')
            self.assertEqual(d.image(ensure_review_document(self.root), 'photo')['alt'], 'Accepted ALT')

    def test_generation_concurrency_is_bounded_and_queued_items_cancel(self):
        entered, release = threading.Event(), threading.Event()
        lock = threading.Lock()
        running = [0, 0]
        def generate(provider, entry, path):
            with lock:
                running[0] += 1
                running[1] = max(running[1], running[0])
                if running[0] == 2: entered.set()
            release.wait(3)
            with lock: running[0] -= 1
            return self.fixture.response(entry)['responses'][0]
        self.addCleanup(release.set)
        with mock.patch.object(d.OllamaProvider, 'generate', generate):
            self.assertEqual(self.post('generate', {'block_ids': ['photo', 'decoration'], 'model': 'mock'}).status_code, 200)
            self.assertTrue(entered.wait(1))
            self.assertEqual(running[1], 2)
            # A third request queues; cancellation must prevent its eventual dispatch.
            self.post('associate', {'block_id': 'ambiguous', 'asset_path': 'extraction/assets/images/one.png'})
            self.post('generate', {'block_ids': ['ambiguous'], 'model': 'mock'})
            queued = next(e for e in self.client.get('/api/image-drafts').json()['entries'] if e['block_id'] == 'ambiguous')
            self.assertEqual(queued['status'], 'requested')
            self.post('cancel', queued)
            release.set()
            time.sleep(.1)
            self.assertLessEqual(running[1], 2)
            store = d.state(ensure_review_document(self.root))
            self.assertEqual(store['requests'][queued['request_id']]['status'], 'cancelled')

    def test_provider_http_payloads_and_explicit_key_are_mocked(self):
        entry = self.fixture.entry(provider='openai', model='gpt-4.1-nano')
        value = self.fixture.response(entry)['responses'][0]
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'choices': [{'message': {'content': json.dumps(value)}}]}).encode()
        opener = mock.MagicMock(); opener.open.return_value = response
        with mock.patch.dict('os.environ', {'PDF_TO_WEB_OPENAI_API_KEY': 'dedicated-fixture-key'}), mock.patch('urllib.request.build_opener', return_value=opener):
            result = d.OpenAIProvider().generate(entry, self.root / entry['asset_path'])
        self.assertEqual(result, value)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.openai.com/v1/chat/completions')
        self.assertEqual(request.get_header('Authorization'), 'Bearer dedicated-fixture-key')
        body = json.loads(request.data)
        self.assertEqual(body['model'], 'gpt-4.1-nano')
        self.assertTrue(body['messages'][0]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'))
        response.__enter__.return_value.read.return_value = json.dumps({'message': {'content': json.dumps(value)}}).encode()
        with mock.patch('urllib.request.build_opener', return_value=opener):
            self.assertEqual(d.OllamaProvider('mock').generate(entry, self.root / entry['asset_path']), value)
        self.assertEqual(opener.open.call_args.args[0].full_url, 'http://127.0.0.1:11434/api/chat')

    def test_confirmed_asset_previews_and_public_document_model(self):
        self.post('associate', {'block_id': 'ambiguous', 'asset_path': 'extraction/assets/images/two.png'})
        html = self.client.get('/api/preview/html').text
        self.assertIn('/api/image-drafts/asset?path=extraction/assets/images/two.png', html)
        from pdf_to_web.web import _document_with_local_preview_media
        projected = _document_with_local_preview_media(ensure_review_document(self.root))
        self.assertEqual(d.image(projected, 'ambiguous')['wordpress_url'], '/api/image-drafts/asset?path=extraction/assets/images/two.png')
        self.assertNotIn('project_dir', self.client.get('/api/document').json())

    def test_both_undo_routes_cancel_late_provider_results(self):
        for route in ('/api/review/undo', '/api/output-pages/undo'):
            entered, release = threading.Event(), threading.Event()
            self.addCleanup(release.set)
            def generate(provider, entry, path):
                entered.set(); release.wait(3)
                return self.fixture.response(entry)['responses'][0]
            with mock.patch.object(d.OllamaProvider, 'generate', generate):
                self.post('generate', {'block_ids': ['photo'], 'model': 'mock', 'regenerate': True})
                self.assertTrue(entered.wait(1))
                self.client.post('/api/blocks/p', headers=self.headers, json={'content': 'Temporary edit'})
                result = self.client.post(route, headers=self.headers, json={})
                self.assertEqual(result.status_code, 200, result.text)
                release.set()
                self.wait_status('cancelled')
                self.assertEqual(d.image(ensure_review_document(self.root), 'photo')['alt'], 'Accepted ALT')

    def test_provider_settings_save_reopen_and_undo_without_generation(self):
        before = ensure_review_document(self.root)
        result = self.post('settings', {'provider': 'openai', 'model': 'llava:latest'})
        self.assertEqual(result.status_code, 200, result.text)
        doc = ensure_review_document(self.root)
        self.assertEqual(d.state(doc)['settings']['provider'], 'openai')
        self.assertEqual(doc['blocks'], before['blocks'])
        self.assertEqual(d.state(doc)['requests'], {})
        self.assertIn('<option value="openai" selected>', self.client.get('/structure').text)
        self.client.post('/api/review/undo', headers=self.headers, json={})
        self.assertNotIn('settings', d.state(ensure_review_document(self.root)))
        self.post('settings', {'provider': 'manual', 'model': 'llava:latest'})
        self.assertIn('<option value="manual" selected>', self.client.get('/structure').text)
        self.assertEqual(self.post('settings', {'provider': 'unknown', 'model': ''}).status_code, 400)
