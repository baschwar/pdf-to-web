import copy
import unittest
import test_web_app as fixtures
from test_page_grouping import block, document
from pdf_to_web import output_pages as op
from pdf_to_web.page_grouping import auto_slug, group_title, plan
from pdf_to_web.review_state import ensure_review_document, review_path, save_review_document


class PageTitleTests(unittest.TestCase):
    def test_first_included_h1_or_h2_uses_review_order_and_skips_excluded_ancestors(self):
        d = document()
        d['blocks'] = [block('excluded', 1, type='heading', level=1, content='Excluded', excluded=True),
            block('wrapper', 1, excluded=True, children=[block('child', 1, type='heading', level=1, content='Hidden child')]),
            block('h2', 1, type='heading', level=2, content='  First\nheading  '),
            block('h1', 1, type='heading', level=1, content='Later H1')]
        self.assertEqual(group_title(d, ['h1', 'h2', 'excluded', 'wrapper'], 'Fallback'), 'First heading')

    def test_source_heading_and_numbered_fallback_titles_and_unique_slugs(self):
        d = document()
        d['blocks'] = [block('h1', 1, type='heading', level=1, content='Repeated title'),
            block('h2', 2, type='heading', level=2, content='Repeated title'), block('p', 3)]
        d['output_pages']['pages'][0]['block_ids'] = ['h1', 'h2', 'p']
        source = plan(d, 4, 'source')
        self.assertEqual([p['title'] for p in source['pages']], ['Repeated title', 'Repeated title', 'Source page 3', 'Source page 4'])
        self.assertEqual(len({p['slug'] for p in source['pages']}), 4)
        headings = plan(d, 4, 'headings', selected=[0, 1])
        self.assertEqual([p['title'] for p in headings['pages'][1:]], ['Repeated title', 'Repeated title'])
        self.assertEqual(len({p['slug'] for p in headings['pages']}), 3)

    def test_merged_provenance_does_not_guess_heading_from_paragraph_text(self):
        d = document()
        d['blocks'] = [block('a', 1, content='Paragraph containing old heading text', provenance={'source_page': 1, 'merged_source_pages': [1, 2]}),
            block('h', 1, type='heading', level=2, content='Actual reviewed heading')]
        d['output_pages']['pages'][0]['block_ids'] = ['a', 'h']
        result = plan(d, 2, 'source', choices={'a': 1})
        self.assertEqual(result['pages'][0]['title'], 'Custom')  # exact match keeps intentional metadata
        self.assertEqual(group_title(d, ['a', 'h'], 'Fallback'), 'Actual reviewed heading')
        self.assertEqual(group_title(d, ['a'], 'Fallback'), 'Fallback')

    def legacy(self):
        d = document()
        d['blocks'][0].update(type='heading', level=2, content='First source heading')
        d['blocks'][1].update(type='heading', level=1, content='Second source heading')
        d['output_pages']['pages'] = plan(d, 2, 'source')['pages']
        for i, p in enumerate(d['output_pages']['pages'], 1):
            p['title'] = f'Report — Page {i}'
            p['slug'] = auto_slug(p['title'])
            p.pop('title_mode'); p.pop('generated_title')
        return d

    def test_legacy_refresh_is_pure_preserves_assignments_and_custom_title_slug(self):
        d = self.legacy()
        d['output_pages']['pages'][1]['title'] = 'My authored title'
        d['output_pages']['pages'][1]['slug'] = 'my-authored-slug'
        d['output_pages']['pages'][1]['slug_mode'] = 'custom'
        before = copy.deepcopy(d)
        result = plan(d, 2, 'titles')
        self.assertEqual(d, before)
        self.assertEqual(result['pages'][0]['title'], 'First source heading')
        self.assertEqual(result['pages'][0]['slug'], 'first-source-heading')
        self.assertEqual(result['pages'][1], before['output_pages']['pages'][1])
        self.assertEqual([p['block_ids'] for p in result['pages']], [['a'], ['b']])
        self.assertEqual(result['moves'], [])
        self.assertTrue(result['can_apply'])

    def test_tracked_auto_title_with_manual_slug_refreshes_without_rewriting_slug(self):
        d = self.legacy()
        first = d['output_pages']['pages'][0]
        first.update(slug_mode='custom', slug='keep-this-url')
        refreshed = plan(d, 2, 'titles')
        self.assertEqual(refreshed['pages'][0]['slug'], 'keep-this-url')
        d['output_pages']['pages'] = refreshed['pages']
        self.assertFalse(plan(d, 2, 'titles')['can_apply'])
        external_edit = copy.deepcopy(d)
        external_edit['output_pages']['pages'][0]['title'] = 'Report — Page 1'
        self.assertEqual(plan(external_edit, 2, 'titles')['pages'][0]['title'], 'Report — Page 1')
        op.mutate(d, 'metadata', {'page_id': first['id'], 'title': 'Intentional override', 'slug_mode': 'custom', 'slug': 'keep-this-url'})
        d['blocks'][0]['content'] = 'Heading changed again'
        self.assertEqual(plan(d, 2, 'titles')['pages'][0]['title'], 'Intentional override')

    def test_reconstruction_placeholder_and_unrecognized_empty_draft_keep_labels(self):
        d = self.legacy()
        p = op.new_page('Source page 3 — needs manual reconstruction', manual_reconstruction_source_page=3)
        extra = op.new_page('My empty draft')
        d['output_pages']['pages'].extend([p, extra])
        result = plan(d, 3, 'titles')
        self.assertEqual(result['pages'][-2:], [p, extra])


class PageTitleRouteTests(unittest.TestCase):
    setUp = fixtures.WebAppTests.setUp
    bootstrap = fixtures.WebAppTests.bootstrap
    headers = fixtures.WebAppTests.headers

    def test_refresh_preview_apply_reopen_and_undo_preserve_reviewed_content(self):
        self.bootstrap()
        d = ensure_review_document(self.project)
        d['blocks'][2].update(type='heading', level=2, content='Second page heading')
        d['output_pages']['pages'] = plan(d, 2, 'source')['pages']
        for i, p in enumerate(d['output_pages']['pages'], 1):
            p['title'] = f'Web fixture — Page {i}'; p['slug'] = auto_slug(p['title'])
            p.pop('title_mode'); p.pop('generated_title')
        before = save_review_document(self.project, d, snapshot=False)
        raw = review_path(self.project).read_bytes()
        response = self.client.post('/api/page-grouping/preview', headers=self.headers(), json={'method': 'titles'})
        self.assertEqual(response.status_code, 200, response.text)
        preview = response.json()
        self.assertEqual(review_path(self.project).read_bytes(), raw)
        self.assertEqual(preview['proposal']['moves'], [])
        result = self.client.post('/api/page-grouping/apply', headers=self.headers(), json={'method': 'titles',
            'expected_review_token': preview['expected_review_token'], 'proposal_digest': preview['proposal_digest']})
        self.assertEqual(result.status_code, 200, result.text)
        after = ensure_review_document(self.project)
        self.assertEqual(after['blocks'], before['blocks'])
        self.assertEqual(after['review'], before['review'])
        self.assertEqual([p['title'] for p in op.pages(after)], ['Web fixture', 'Second page heading'])
        self.assertEqual([p['block_ids'] for p in op.pages(after)], [p['block_ids'] for p in op.pages(before)])
        self.assertEqual(self.client.get('/output-pages').status_code, 200)
        self.assertIn('Preview generated page titles', self.client.get('/output-pages').text)
        self.assertEqual(self.client.post('/api/output-pages/undo', headers=self.headers(), json={}).status_code, 200)
        self.assertEqual(op.pages(ensure_review_document(self.project)), op.pages(before))


if __name__ == '__main__':
    unittest.main()
