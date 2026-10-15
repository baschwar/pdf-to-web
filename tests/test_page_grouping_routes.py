import copy
import json
import unittest
import xml.etree.ElementTree as ET
import test_web_app as fixtures

from pdf_to_web import output_pages as op
from pdf_to_web.image_review import review_token
from pdf_to_web.manual_reconstruction import toggle
from pdf_to_web.page_grouping import auto_slug
from pdf_to_web.review_state import ensure_review_document, review_path, save_review_document


class PageGroupingRouteTests(unittest.TestCase):
    setUp = fixtures.WebAppTests.setUp
    bootstrap = fixtures.WebAppTests.bootstrap
    headers = fixtures.WebAppTests.headers

    def prepare(self):
        self.bootstrap()
        return save_review_document(self.project, ensure_review_document(self.project), snapshot=False)

    def preview(self, **values):
        response = self.client.post('/api/page-grouping/preview', headers=self.headers(), json={'method': 'source', **values})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def apply(self, preview, **values):
        return self.client.post('/api/page-grouping/apply', headers=self.headers(), json={
            'method': 'source', 'expected_review_token': preview['expected_review_token'],
            'proposal_digest': preview['proposal_digest'], **values})

    def test_preview_is_read_only_apply_is_one_undo_and_reopen_preserves_blocks(self):
        before = self.prepare()
        raw = review_path(self.project).read_bytes()
        preview = self.preview()
        self.assertEqual(review_path(self.project).read_bytes(), raw)
        self.assertEqual([p['block_ids'] for p in preview['proposal']['pages']], [['h', 'p1'], ['p2']])
        result = self.apply(preview)
        self.assertEqual(result.status_code, 200, result.text)
        after = ensure_review_document(self.project)
        self.assertEqual(after['blocks'], before['blocks'])
        self.assertEqual(after['review'], before['review'])
        self.assertEqual(after['review_session']['revision'], before['review_session']['revision'] + 1)
        self.assertEqual(self.client.get('/output-pages').status_code, 200)
        self.assertEqual(op.pages(ensure_review_document(self.project)), op.pages(after))
        undone = self.client.post('/api/output-pages/undo', headers=self.headers(), json={})
        self.assertEqual(undone.status_code, 200)
        self.assertEqual(op.pages(ensure_review_document(self.project)), op.pages(before))

    def test_source_built_package_retains_page_content_in_html_gutenberg_and_wxr(self):
        from review_helpers import approve_publication_fixture
        self.prepare()
        self.assertEqual(self.apply(self.preview()).status_code, 200)
        approve_publication_fixture(self.project)
        response = self.client.post('/api/output-pages/export', headers=self.headers(), json={})
        self.assertEqual(response.status_code, 200, response.text)
        root = self.project / 'output/pages'
        manifest = json.loads((root / 'manifest.json').read_text())
        self.assertEqual(len(manifest['pages']), 2)
        for page, expected, absent in zip(manifest['pages'], ['Original one', 'Original two'], ['Original two', 'Original one']):
            for filename in page['files'].values():
                content = (root / filename).read_text()
                self.assertIn(expected, content)
                self.assertNotIn(absent, content)
        items = ET.parse(root / 'publications.xml').findall('./channel/item')
        self.assertEqual(len(items), 2)
        self.assertEqual([item.find('{http://purl.org/rss/1.0/modules/content/}encoded').text.count('Original') for item in items], [1, 1])

    def test_stale_or_changed_proposal_rejected_without_writes(self):
        self.prepare()
        preview = self.preview()
        raw = review_path(self.project).read_bytes()
        altered = self.apply(preview, method='headings', selected=[0])
        self.assertEqual(altered.status_code, 400)
        self.assertEqual(review_path(self.project).read_bytes(), raw)
        doc = ensure_review_document(self.project)
        doc['blocks'][1]['content'] = 'Another tab saved this content'
        save_review_document(self.project, doc)
        new_raw = review_path(self.project).read_bytes()
        stale = self.apply(preview)
        self.assertEqual(stale.status_code, 400)
        self.assertEqual(review_path(self.project).read_bytes(), new_raw)

    def test_source_hold_remains_placeholder_then_restores_refs_on_ordinary_page(self):
        doc = self.prepare()
        held = toggle(self.project, 2, True, review_token(doc))
        identity = held['review']['manual_reconstruction_pages']['2']['placeholder']['id']
        preview = self.preview()
        self.assertTrue(preview['proposal']['can_apply'])
        self.assertEqual(self.apply(preview).status_code, 200)
        built = ensure_review_document(self.project)
        placeholder = op.page_by_id(built, identity)
        self.assertEqual(placeholder['manual_reconstruction_source_page'], 2)
        self.assertEqual(placeholder['block_ids'], ['p2'])
        self.assertTrue(any('reconstruction' in e for e in op.validate(built)))
        restored = toggle(self.project, 2, False, review_token(built))
        page = op.page_by_id(restored, identity)
        self.assertNotIn('manual_reconstruction_source_page', page)
        self.assertEqual(page['block_ids'], ['p2'])
        self.assertEqual(page['slug'], 'source-page-2')
        self.assertEqual(page['approval']['status'], 'needs_review')
        self.assertEqual(op.validate(restored), [])

    def test_selected_heading_groups_keep_unselected_page_metadata_and_assignments(self):
        doc = self.prepare()
        doc['blocks'].insert(2, {'id': 'second-heading', 'type': 'heading', 'level': 2, 'content': 'Second section', 'provenance': {'source_page': 2}})
        old = op.pages(doc)[0]
        old['block_ids'].insert(2, 'second-heading')
        old.update(title='Custom title', slug='custom-slug', type='post')
        old['approval']['note'] = 'Retained reviewer note'
        save_review_document(self.project, doc)
        preview = self.preview(method='headings', selected=[1])
        result = self.apply(preview, method='headings', selected=[1])
        self.assertEqual(result.status_code, 200, result.text)
        saved = ensure_review_document(self.project)
        residual = op.page_by_id(saved, old['id'])
        self.assertEqual(residual['block_ids'], ['h', 'p1'])
        for key in ('title', 'slug', 'type'):
            self.assertEqual(residual[key], old[key])
        self.assertEqual(residual['approval']['note'], 'Retained reviewer note')
        self.assertEqual(saved['blocks'], doc['blocks'])

    def test_source_built_hold_then_single_page_retains_each_reference_once(self):
        doc = self.prepare()
        toggle(self.project, 2, True, review_token(doc))
        self.assertEqual(self.apply(self.preview()).status_code, 200)
        response = self.client.post('/api/output-pages/single_page', headers=self.headers(), json={})
        self.assertEqual(response.status_code, 200, response.text)
        saved = ensure_review_document(self.project)
        refs = [r for p in op.pages(saved) for r in p['block_ids']]
        self.assertEqual(len(refs), len(set(refs)))
        self.assertEqual(set(refs), {'h', 'p1', 'p2'})
        restored = toggle(self.project, 2, False, review_token(saved))
        self.assertEqual(op.validate(restored), [])

    def test_title_slug_uniqueness_and_custom_override_save(self):
        doc = self.prepare()
        response = self.client.post('/api/output-pages/create', headers=self.headers(), json={'title': 'École Déjà Vu'})
        identity = response.json()['page_id']
        data = {'page_id': identity, 'title': 'Contents', 'slug_mode': 'auto', 'slug': 'ignored-client-slug'}
        self.assertEqual(self.client.post('/api/output-pages/metadata', headers=self.headers(), json=data).status_code, 200)
        self.assertEqual(op.page_by_id(ensure_review_document(self.project), identity)['slug'], auto_slug('Contents'))
        data.update(slug_mode='custom', slug='my-custom-url', title='New custom title')
        self.client.post('/api/output-pages/metadata', headers=self.headers(), json=data)
        data['title'] = 'Later title'
        self.client.post('/api/output-pages/metadata', headers=self.headers(), json=data)
        self.assertEqual(op.page_by_id(ensure_review_document(self.project), identity)['slug'], 'my-custom-url')

    def test_incomplete_contents_lists_every_page_and_recovery_links_without_changes(self):
        doc = self.prepare()
        doc['output_pages']['pages'].extend([
            op.new_page('Needs content', slug='invalid slug'),
            op.new_page('Orphan page', [], parent='missing-parent'),
        ])
        save_review_document(self.project, doc)
        raw = review_path(self.project).read_bytes()
        response = self.client.get('/output-pages-contents')
        self.assertEqual(response.status_code, 200)
        for text in ('Incomplete contents preview', 'Needs content', 'Orphan page', 'Preview page', 'assign blocks'):
            self.assertIn(text, response.text)
        self.assertEqual(review_path(self.project).read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
