import unittest
from pathlib import Path
from unittest import mock

from pdf_to_web.project_outputs import preserve_previous_outputs, output_folder, open_output_folder
from pdf_to_web.web import WebAppConfig, create_app
from review_helpers import approve_publication_fixture
import test_web_app as web_fixture


class ProjectOutputTests(unittest.TestCase):
    setUp = web_fixture.WebAppTests.setUp
    bootstrap = web_fixture.WebAppTests.bootstrap
    headers = web_fixture.WebAppTests.headers

    def export(self):
        return self.client.post('/api/export', headers=self.headers(), json={'target': 'html'})

    def test_zero_images_go_directly_from_text_review_to_project_export(self):
        self.bootstrap()
        before = self.client.get('/export').text
        self.assertIn('No included images', before)
        self.assertNotIn('id="media-export-form"', before)
        self.assertNotIn('id="media-wxr-form"', before)
        self.assertNotIn('id="image-draft-toolbar"', self.client.get('/structure').text)
        self.assertEqual(self.export().status_code, 400)
        approve_publication_fixture(self.project)
        result = self.export()
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['output_root'], str(self.project / 'output'))
        for file in result.json()['downloads']:
            self.assertTrue((self.project / file['path']).is_file())

    def test_repeated_export_preserves_previous_output_and_source(self):
        self.bootstrap()
        approve_publication_fixture(self.project)
        source = (self.project / 'source/original.pdf').read_bytes()
        first = self.export().json()
        file = self.project / first['files'][0]
        contents = file.read_bytes()
        prior_snapshots = set((self.project / 'output/history').iterdir())
        self.assertEqual(self.export().status_code, 200)
        snapshots = list(set((self.project / 'output/history').iterdir()) - prior_snapshots)
        self.assertEqual(len(snapshots), 1)
        saved = snapshots[0] / file.relative_to(self.project / 'output')
        self.assertEqual(saved.read_bytes(), contents)
        self.assertEqual(self.client.get('/download/' + str(saved.relative_to(self.project))).status_code, 404)
        self.assertEqual((self.project / 'source/original.pdf').read_bytes(), source)

    def test_opener_requires_session_origin_csrf_and_current_project(self):
        with mock.patch('pdf_to_web.web.open_output_folder') as opener:
            path = str(self.project.resolve())
            self.assertEqual(self.client.post('/api/output-folder/open', json={'project_root': path}).status_code, 401)
            self.bootstrap()
            self.assertEqual(self.client.post('/api/output-folder/open', json={'project_root': path}).status_code, 403)
            self.assertEqual(self.client.post('/api/output-folder/open', headers=self.headers(), json={'project_root': path + '-other'}).status_code, 400)
            opener.assert_not_called()
            opener.return_value = self.project / 'output'
            self.assertEqual(self.client.post('/api/output-folder/open', headers=self.headers(), json={'project_root': path}).status_code, 200)
            opener.assert_called_once_with(self.project)

    def test_no_active_project_and_opener_failure_are_actionable(self):
        self.bootstrap()
        with mock.patch('pdf_to_web.web.open_output_folder', side_effect=ValueError('Use the displayed path')):
            result = self.client.post('/api/output-folder/open', headers=self.headers(), json={'project_root': str(self.project)})
            self.assertEqual(result.status_code, 400)
            self.assertIn('displayed path', result.json()['error'])
        cfg = WebAppConfig(projects_root=Path(self.tmp.name), recent_store=Path(self.tmp.name) / 'empty-recent.json', port=54321, bootstrap_token='bootstrap', session_token='session', csrf_token='csrf')
        from fastapi.testclient import TestClient
        client = TestClient(create_app(cfg), base_url='http://127.0.0.1:54321')
        client.get('/bootstrap/bootstrap')
        self.assertEqual(client.post('/api/output-folder/open', headers=self.headers(), json={}).json()['detail'], 'Choose a project first')

    def test_spaces_preserved_native_opener_receives_one_path_argument(self):
        folder = self.project / 'output'
        folder.mkdir(exist_ok=True)
        with mock.patch('pdf_to_web.project_outputs.sys.platform', 'darwin'), mock.patch('pdf_to_web.project_outputs.subprocess.run') as run:
            run.return_value.returncode = 0
            self.assertEqual(open_output_folder(self.project), folder)
            self.assertEqual(run.call_args.args[0], ['/usr/bin/open', str(folder)])

    def test_output_collisions_symlinks_and_failed_preservation_do_not_replace_files(self):
        folder = self.project / 'output'
        file = folder / 'html/old.html'
        file.write_text('previous output')
        with mock.patch('pdf_to_web.project_outputs.shutil.copytree', side_effect=PermissionError('fixture')):
            with self.assertRaisesRegex(ValueError, 'No new export was started'):
                preserve_previous_outputs(self.project)
        self.assertEqual(file.read_text(), 'previous output')
        (folder / 'escape').symlink_to(Path(self.tmp.name))
        with self.assertRaisesRegex(ValueError, 'symbolic link'):
            output_folder(self.project)

    def test_all_export_api_results_name_the_same_project_output_root(self):
        self.bootstrap()
        approve_publication_fixture(self.project)
        for endpoint, payload in [('/api/export', {'target': 'gutenberg'}), ('/api/export', {'target': 'wordpress-xml'}), ('/api/accessibility-report', {}), ('/api/output-pages/export', {}), ('/api/media-export', {'image_prefix': 'fixture-'})]:
            result = self.client.post(endpoint, headers=self.headers(), json=payload)
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()['output_root'], str(self.project / 'output'))
            for file in result.json()['downloads']:
                self.assertTrue((self.project / file['path']).is_file())


if __name__ == '__main__':
    unittest.main()
