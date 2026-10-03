"""Destination ownership checks using disposable PDFs and projects."""
import base64
from dataclasses import replace
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient
from pdf_to_web.errors import PdfToWebError
from pdf_to_web.extraction import run_extraction
from pdf_to_web.normalize import normalize_project
from pdf_to_web.project import create_project, import_pdf, load_project
from pdf_to_web.review_state import ensure_review_document, update_block, undo_last
from pdf_to_web.web import CSRF_HEADER, WebAppConfig, create_app
from review_helpers import approve_publication_fixture

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aB1sAAAAASUVORK5CYII=')


def synthetic_pdf(path):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    content = DecodedStreamObject()
    content.set_data(b'BT /F1 12 Tf 54 720 Td (Synthetic destination fixture with sufficient readable text for review and export.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(content)
    writer.write(path)
    return path


def synthetic_engine(command, **kwargs):
    """Replace only the external Java process; real extraction bookkeeping stays."""
    raw = Path(command[command.index('--output-dir') + 1])
    images = Path(command[command.index('--image-dir') + 1])
    source = Path(command[3])
    root = raw.parent.parent
    assert source.is_relative_to(root) and images.is_relative_to(root)
    (images / 'fixture.png').write_bytes(PNG)
    data = {'file name': source.name, 'number of pages': 1, 'title': 'Destination fixture', 'kids': [
        {'id': 1, 'type': 'heading', 'level': 1, 'text': 'Destination fixture', 'page number': 1},
        {'id': 2, 'type': 'paragraph', 'text': 'Synthetic destination content.', 'page number': 1},
        {'id': 3, 'type': 'image', 'source': 'images/fixture.png', 'page number': 1},
    ]}
    (raw / 'fixture.json').write_text(json.dumps(data))
    (raw / 'fixture.md').write_text('# Destination fixture\n\nSynthetic destination content.')
    return subprocess.CompletedProcess(command, 0, 'Synthetic engine only\n', '')


def extract_fixture(root, *args):
    with mock.patch('pdf_to_web.extraction.find_supported_java', return_value=(Path('/synthetic/java'), 'synthetic')), \
         mock.patch('pdf_to_web.extraction.java_environment', return_value={}), \
         mock.patch('pdf_to_web.extraction.subprocess.run', side_effect=synthetic_engine):
        return run_extraction(root, *args)


class ProjectDestinationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()

    def test_scaffold_preserves_loose_files_and_uses_source_already_in_root(self):
        root = self.base / 'Chosen é folder'
        pdf = synthetic_pdf(root / 'Input café.pdf')
        (root / 'notes.txt').write_text('keep')
        original = pdf.read_bytes()
        create_project(root, 'Different project name')
        import_pdf(root, pdf)
        self.assertEqual(pdf.read_bytes(), original)
        self.assertEqual((root / 'source' / pdf.name).read_bytes(), original)
        self.assertEqual((root / 'notes.txt').read_text(), 'keep')
        for name in ('extraction/raw/images', 'extraction/assets/images', 'extraction/normalized', 'review/revisions', 'review/source-pages', 'output/html', 'output/wordpress/wxr'):
            self.assertTrue((root / name).is_dir(), name)
        self.assertFalse((root / 'different-project-name').exists())

    def test_source_already_in_source_is_used_in_place(self):
        root = self.base / 'in place'
        pdf = synthetic_pdf(root / 'source' / 'Existing.pdf')
        inode = pdf.stat().st_ino
        create_project(root)
        import_pdf(root, pdf)
        self.assertEqual(pdf.stat().st_ino, inode)
        self.assertEqual(list((root / 'source').glob('*.pdf')), [pdf])

    def test_existing_source_filename_collision_preserves_both_pdfs(self):
        root = self.base / 'collision'
        prior = synthetic_pdf(root / 'source/Input.pdf')
        old = prior.read_bytes()
        new = synthetic_pdf(self.base / 'input/Input.pdf')
        new.write_bytes(new.read_bytes() + b'\n% separate input\n')
        create_project(root)
        import_pdf(root, new)
        self.assertEqual(prior.read_bytes(), old)
        self.assertEqual((root / 'source/Input-2.pdf').read_bytes(), new.read_bytes())
        self.assertEqual(load_project(root)['source']['path'], 'source/Input-2.pdf')

    def test_existing_working_entries_and_source_links_rejected_without_changes(self):
        for kind in ('project.json', 'extraction', 'review', 'output', 'source'):
            with self.subTest(kind=kind):
                root = self.base / kind.replace('.', '-')
                root.mkdir()
                entry = root / kind
                if kind == 'source':
                    entry.symlink_to(self.base / 'missing', target_is_directory=True)
                else:
                    entry.write_text('untouched')
                with self.assertRaises(PdfToWebError):
                    create_project(root)
                self.assertEqual(list(root.iterdir()), [entry])
                if kind != 'source': self.assertEqual(entry.read_text(), 'untouched')

    def test_permission_failure_rolls_back_only_owned_empty_directories(self):
        root = self.base / 'restricted'
        root.mkdir()
        (root / 'notes.txt').write_text('keep')
        real_mkdir = Path.mkdir
        def denied(path, *args, **kwargs):
            if path.name == 'normalized': raise PermissionError('Synthetic permission denied')
            return real_mkdir(path, *args, **kwargs)
        with mock.patch.object(Path, 'mkdir', denied), self.assertRaises(PermissionError):
            create_project(root)
        self.assertEqual([p.name for p in root.iterdir()], ['notes.txt'])

    def test_source_copy_rejects_escape_after_scaffold(self):
        root = self.base / 'safe'
        create_project(root)
        (root / 'source').rmdir()
        outside = self.base / 'outside'; outside.mkdir()
        (root / 'source').symlink_to(outside, target_is_directory=True)
        pdf = synthetic_pdf(self.base / 'original.pdf')
        with self.assertRaises(PdfToWebError): import_pdf(root, pdf)
        self.assertEqual(list(outside.iterdir()), [])


class DestinationRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.previous = self.base / 'previous'
        create_project(self.previous)
        import_pdf(self.previous, synthetic_pdf(self.base / 'previous.pdf'))
        extract_fixture(self.previous)
        normalize_project(self.previous)
        ensure_review_document(self.previous)
        self.previous_bytes = (self.previous / 'review/current.json').read_bytes()
        self.chosen = self.base / 'Exact chosen café 空间'; self.chosen.mkdir()
        self.input = synthetic_pdf(self.base / 'input folder' / 'Input café.pdf')
        self.input_bytes = self.input.read_bytes()
        self.config = WebAppConfig(project=self.previous, recent_projects=(self.previous,), projects_root=self.base / 'default', recent_store=self.base / 'recents.json', port=54321, bootstrap_token='b', session_token='s', csrf_token='c')
        self.client = self.new_client()

    def new_client(self):
        client = TestClient(create_app(replace(self.config, bootstrap_used=False)), base_url='http://127.0.0.1:54321')
        client.get('/bootstrap/b')
        return client

    def post(self, route, payload=None):
        return self.client.post(route, json=payload or {}, headers={'Origin': 'http://127.0.0.1:54321', CSRF_HEADER: 'c'})

    def choose(self):
        with mock.patch('pdf_to_web.web.choose_project_folder', return_value=self.chosen) as picker:
            response = self.post('/api/picker/destination')
            picker.assert_called_once_with(destination=True)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(list(self.chosen.iterdir()), [])
        return response.json()['destination']['token']

    def create(self, token, **overrides):
        with mock.patch('pdf_to_web.web.choose_pdf_file', return_value=self.input), \
             mock.patch('pdf_to_web.web.run_extraction', side_effect=extract_fixture):
            return self.post('/api/projects/create', {'title': 'Title differs from root', 'destination_mode': 'chosen', 'destination_token': token, **overrides})

    def assert_previous_preserved(self):
        self.assertEqual((self.previous / 'review/current.json').read_bytes(), self.previous_bytes)
        self.assertEqual(self.input.read_bytes(), self.input_bytes)
        self.assertFalse(self.config.projects_root.exists())

    def test_exact_unicode_root_create_reopen_history_cache_previews_and_exports(self):
        response = self.create(self.choose())
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['project']['path'], str(self.chosen))
        self.assertEqual((self.chosen / 'source' / self.input.name).read_bytes(), self.input_bytes)
        self.assertTrue((self.chosen / 'extraction/assets/manifest.json').is_file())
        update_block(self.chosen, 'odl-2', {'content': 'Edited locally'})
        self.assertTrue(any((self.chosen / 'review/revisions').glob('*.json')))
        undo_last(self.chosen)
        (self.chosen / 'review/source-pages/page-0001.png').write_bytes(PNG)
        self.assertEqual(self.client.get('/source-page/1.png').content, PNG)
        for page in ('/', '/document', '/structure', '/accessibility', '/output-pages', '/preview', '/export'):
            self.assertIn(str(self.chosen), self.client.get(page).text, page)
        approve_publication_fixture(self.chosen)
        self.assertIn('Synthetic destination content.', self.client.get('/api/preview/html').text)
        for target in ('html', 'gutenberg', 'wordpress-xml'):
            exported = self.post('/api/export', {'target': target})
            self.assertEqual(exported.status_code, 200, exported.text)
            self.assertEqual(exported.json()['project_root'], str(self.chosen))
            for item in exported.json()['downloads']:
                self.assertTrue((self.chosen / item['path']).is_file())
                self.assertEqual(self.client.get(item['url']).status_code, 200)
        package = self.post('/api/output-pages/export')
        self.assertEqual(package.status_code, 200, package.text)
        self.assertTrue((self.chosen / 'output/pages.zip').is_file())
        self.client = self.new_client()
        with mock.patch('pdf_to_web.web.choose_project_folder', return_value=self.chosen):
            token = self.post('/api/picker/project').json()['selection']['token']
        opened = self.post('/api/projects/open', {'selection_token': token})
        self.assertEqual(opened.json()['next'], '/document')
        self.assertIn(str(self.chosen), self.client.get('/document').text)
        self.assertIn(str(self.chosen), [p['path'] for p in json.loads((self.base / 'recents.json').read_text())['projects']])
        self.assert_previous_preserved()

    def test_invalid_expired_raw_path_or_inconsistent_choice_never_uses_default(self):
        for data in ({'destination_mode': 'chosen'}, {'destination_mode': 'chosen', 'destination_token': 'forged'}, {'destination_path': str(self.chosen)}, {'destination_mode': 'other'}, {'destination_mode': 'default', 'destination_token': 'stale'}):
            with self.subTest(data=data), mock.patch('pdf_to_web.web.choose_pdf_file') as picker:
                result = self.post('/api/projects/create', {'title': 'Name', **data})
                self.assertEqual(result.status_code, 400)
                picker.assert_not_called()
                self.assertEqual(list(self.chosen.iterdir()), [])
        token = self.choose()
        self.client = self.new_client()
        result = self.create(token)
        self.assertEqual(result.status_code, 400)
        self.assertIn('No default folder was used', result.json()['error'])
        self.assert_previous_preserved()

    def test_folder_and_pdf_cancel_make_no_files_and_keep_previous_project(self):
        screen = self.client.get('/').text
        self.assertLess(screen.index('id="project-message"'), screen.index('id="recent-heading"'))
        with mock.patch('pdf_to_web.web.choose_project_folder', side_effect=PdfToWebError('Folder selection cancelled')):
            self.assertEqual(self.post('/api/picker/destination').status_code, 400)
        token = self.choose()
        with mock.patch('pdf_to_web.web.choose_pdf_file', side_effect=PdfToWebError('PDF selection cancelled')):
            response = self.post('/api/projects/create', {'title': 'Name', 'destination_mode': 'chosen', 'destination_token': token})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(list(self.chosen.iterdir()), [])
        self.assertIn(str(self.previous), self.client.get('/document').text)
        self.assert_previous_preserved()

    def test_conflict_created_after_choice_is_rejected_without_modification(self):
        token = self.choose()
        (self.chosen / 'output').mkdir()
        (self.chosen / 'output/keep.txt').write_text('keep')
        with mock.patch('pdf_to_web.web.choose_pdf_file') as picker:
            result = self.post('/api/projects/create', {'title': 'Name', 'destination_mode': 'chosen', 'destination_token': token})
            picker.assert_not_called()
        self.assertEqual(result.status_code, 400)
        self.assertFalse((self.chosen / 'project.json').exists())
        self.assertEqual((self.chosen / 'output/keep.txt').read_text(), 'keep')
        self.assert_previous_preserved()

    def test_copy_failure_retains_partial_project_and_actionable_permissions_error(self):
        token = self.choose()
        with mock.patch('pdf_to_web.project.shutil.copy2', side_effect=PermissionError('Synthetic denied')):
            response = self.create(token)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Check folder permissions', response.json()['error'])
        self.assertIn(str(self.chosen), response.json()['error'])
        self.assertTrue((self.chosen / 'project.json').is_file())
        self.assertIn(str(self.previous), self.client.get('/document').text)
        self.assert_previous_preserved()

    def test_extraction_and_normalization_failure_partial_reopen_then_recovery(self):
        token = self.choose()
        with mock.patch('pdf_to_web.web.choose_pdf_file', return_value=self.input), mock.patch('pdf_to_web.web.run_extraction', side_effect=PdfToWebError('Synthetic extraction failed')):
            result = self.post('/api/projects/create', {'title': 'Name', 'destination_mode': 'chosen', 'destination_token': token})
        self.assertEqual(result.status_code, 400)
        self.assertIn('previous project remains open', result.json()['error'])
        self.assertIn(str(self.previous), self.client.get('/document').text)
        self.assertEqual((self.chosen / 'source' / self.input.name).read_bytes(), self.input_bytes)
        with mock.patch('pdf_to_web.web.choose_project_folder', return_value=self.chosen):
            selection = self.post('/api/picker/project').json()['selection']['token']
        self.assertEqual(self.post('/api/projects/open', {'selection_token': selection}).json()['next'], '/')
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Conversion incomplete', page.text)
        self.assertIn('Synthetic extraction failed', page.text)
        extract_fixture(self.chosen)
        normalize_project(self.chosen)
        self.assertEqual(self.post('/api/projects/open', {'selection_token': selection}).json()['next'], '/document')
        self.assertEqual(self.client.get('/document').status_code, 200)
        self.assert_previous_preserved()

    def test_normalization_failure_keeps_extraction_in_chosen_root(self):
        token = self.choose()
        with mock.patch('pdf_to_web.web.normalize_project', side_effect=PdfToWebError('Synthetic normalization failed')):
            response = self.create(token)
        self.assertEqual(response.status_code, 400)
        self.assertTrue((self.chosen / 'extraction/raw/fixture.json').is_file())
        self.assertIn(str(self.previous), self.client.get('/document').text)
        self.assert_previous_preserved()

    def test_partial_metadata_failure_does_not_hide_original_error(self):
        token = self.choose()
        def corrupt_then_fail(root, *_):
            (root / 'project.json').write_text('invalid metadata')
            raise PdfToWebError('Original conversion error')
        with mock.patch('pdf_to_web.web.choose_pdf_file', return_value=self.input), mock.patch('pdf_to_web.web.run_extraction', side_effect=corrupt_then_fail):
            result = self.post('/api/projects/create', {'title': 'Name', 'destination_mode': 'chosen', 'destination_token': token})
        self.assertEqual(result.status_code, 400)
        self.assertIn('Original conversion error', result.json()['error'])
        self.assertIn(str(self.previous), self.client.get('/document').text)
        self.assert_previous_preserved()

    def test_explicit_default_uses_displayed_named_default(self):
        with mock.patch('pdf_to_web.web.choose_pdf_file', return_value=self.input), mock.patch('pdf_to_web.web.run_extraction', side_effect=extract_fixture):
            result = self.post('/api/projects/create', {'title': 'Default Folder', 'destination_mode': 'default'})
        expected = self.config.projects_root / 'default-folder'
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['project']['path'], str(expected))
        self.assertTrue((expected / 'review/current.json').is_file())
        self.assertEqual(self.input.read_bytes(), self.input_bytes)
        self.assertEqual(list(self.chosen.iterdir()), [])

    def test_recent_store_failure_warns_without_blocking_create_or_open(self):
        token = self.choose()
        with mock.patch('pdf_to_web.web.remember_project', side_effect=PermissionError('Global recent store denied')):
            response = self.create(token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn(str(self.config.recent_store), response.json()['warning'])
        self.assertIn(str(self.chosen), self.client.get('/document').text)
        with mock.patch('pdf_to_web.web.choose_project_folder', return_value=self.chosen):
            selection = self.post('/api/picker/project').json()['selection']['token']
        with mock.patch('pdf_to_web.web.remember_project', side_effect=PermissionError('Global recent store denied')):
            opened = self.post('/api/projects/open', {'selection_token': selection})
        self.assertEqual(opened.status_code, 200)
        self.assertIn('Recent projects list', opened.json()['warning'])
        self.assert_previous_preserved()

    def test_restart_with_project_succeeds_when_global_recents_are_unwritable(self):
        with mock.patch('pdf_to_web.web.remember_project', side_effect=PermissionError('Global recent store denied')):
            client = self.new_client()
        self.assertEqual(client.get('/document').status_code, 200)
        self.assertIn('Recent projects list could not be updated', client.get('/').text)
        self.assertEqual((self.previous / 'review/current.json').read_bytes(), self.previous_bytes)
