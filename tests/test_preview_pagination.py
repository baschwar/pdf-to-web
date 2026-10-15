"""Page preview navigation is read-only and retains the existing projections."""
import unittest
import test_web_app as fixtures
from pdf_to_web import output_pages as op
from pdf_to_web.review_state import ensure_review_document, save_review_document, review_path

class PreviewPaginationTests(unittest.TestCase):
    setUp = fixtures.WebAppTests.setUp
    bootstrap = fixtures.WebAppTests.bootstrap

    def prepare(self):
        self.bootstrap()
        doc = ensure_review_document(self.project)
        doc['output_pages']['pages'] = [op.new_page('First', ['h', 'p1'], navigation_order=0), op.new_page('Second', ['p2'], navigation_order=1), op.new_page('Empty', [], navigation_order=2)]
        save_review_document(self.project, doc, snapshot=False)
        return doc

    def test_selected_page_profile_mode_and_read_only_preview(self):
        doc = self.prepare(); before = review_path(self.project).read_bytes()
        second = op.pages(doc)[1]
        response = self.client.get('/preview', params={'page_id': second['id'], 'mode': 'semantic', 'profile': 'wsuwp'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'value="{second["id"]}" data-slug="second" data-state="" selected', response.text)
        self.assertIn('data-mode="semantic" data-profile="wsuwp"', response.text)
        self.assertIn('/output-preview/second.html?mode=semantic&amp;profile=wsuwp', response.text)
        rendered = self.client.get('/output-preview/second.html').text
        self.assertIn('Original two', rendered); self.assertNotIn('Original one', rendered)
        self.assertEqual(review_path(self.project).read_bytes(), before)

    def test_whole_document_choice_survives_reload(self):
        self.prepare()
        text = self.client.get('/preview?page_id=&mode=semantic').text
        self.assertIn('src="/api/preview/html"', text)
        self.assertNotIn('data-state="" selected', text)

    def test_empty_and_reconstruction_pages_remain_visible(self):
        doc = self.prepare()
        p = op.new_page('Held', [], navigation_order=3); p['manual_reconstruction_source_page'] = 2
        doc['review']['manual_reconstruction_pages'] = {'2': {'blocks': {}, 'shared_block_ids': [], 'placeholder': p}}; doc['output_pages']['pages'].append(p); save_review_document(self.project, doc, snapshot=False)
        text = self.client.get('/preview').text
        self.assertIn('Incomplete: no included content', text)
        self.assertIn('Unfinished reconstruction', text)
        self.assertIn('4. Held', text)

    def test_arrangement_retains_saved_slug_and_compact_controls(self):
        doc = self.prepare()
        text = self.client.get('/output-pages', params={'page_id': op.pages(doc)[1]['id']}).text
        self.assertIn('data-page-slug="second"', text)
        for name in ['page-metadata-grid', 'page-arrangement-actions', 'page-merge-row', 'output-page-add-content', 'output-page-approval']:
            self.assertIn(name, text)

    def test_continue_is_inside_expanded_workspace(self):
        from html.parser import HTMLParser
        self.prepare()
        class Links(HTMLParser):
            def __init__(self): super().__init__(); self.inside = False; self.found = False
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if values.get('id') == 'preview-workspace': self.inside = True
                if 'data-preview-export' in values and self.inside: self.found = True
            def handle_endtag(self, tag):
                if tag == 'section': self.inside = False
        parser = Links(); parser.feed(self.client.get('/preview').text)
        self.assertTrue(parser.found)

    def test_export_context_preserves_return_page_without_generating_outputs(self):
        doc = self.prepare(); before = review_path(self.project).read_bytes()
        p = op.pages(doc)[1]
        outputs_before = {str(f): f.read_bytes() for f in (self.project / 'output').rglob('*') if f.is_file()}
        response = self.client.get('/export', params={'page_id': p['id'], 'mode': 'semantic', 'profile': 'wsuwp'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('From Preview: <strong>Second</strong>', response.text)
        self.assertIn(f'/preview?page_id={p["id"]}&amp;mode=semantic&amp;profile=wsuwp', response.text)
        self.assertIn('covers the whole document', response.text)
        self.assertEqual(review_path(self.project).read_bytes(), before)
        self.assertEqual({str(f): f.read_bytes() for f in (self.project / 'output').rglob('*') if f.is_file()}, outputs_before)
