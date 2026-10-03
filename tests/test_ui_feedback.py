from review_helpers import stamp_fixture_approvals, approve_publication_fixture
import copy
import json
import re
import unittest

import test_image_draft_routes as routes
from pdf_to_web.accessibility import assess_document, visual_readiness
from pdf_to_web.exporters import html, gutenberg
from pdf_to_web.exporters.common import publication_document
from pdf_to_web.export_validation import validate_project_exports
from pdf_to_web.project import load_project, save_project
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, update_complex_visual, undo_last


class PublicationHeadingTests(unittest.TestCase):
    def document(self):
        return {'metadata': {'title': 'Guide'}, 'blocks': [
            {'id': 'title', 'type': 'heading', 'level': 1, 'content': 'Guide'},
            {'id': 'a', 'type': 'heading', 'level': 4, 'content': 'Account'},
            {'id': 'b', 'type': 'heading', 'level': 1, 'content': 'Courses'},
            {'id': 'c', 'type': 'heading', 'level': 5, 'content': 'Finish'},
            {'id': 'excluded', 'type': 'heading', 'level': 1, 'content': 'Ignore', 'review': {'status': 'excluded'}},
        ]}

    def test_one_title_and_no_heading_skips_without_changing_source(self):
        document = self.document()
        before = copy.deepcopy(document)
        self.assertEqual([b['level'] for b in publication_document(document)['blocks'][:-1]], [1, 2, 2, 3])
        for markup in (html.render_document(document), gutenberg.render_document(document)):
            self.assertEqual(len(re.findall(r'<h1(?:\s|>)', markup)), 1)
            self.assertIn('<h2', markup)
            self.assertNotIn('<h4', markup)
            self.assertNotIn('Ignore', markup)
        self.assertEqual(document, before)

    def test_template_title_and_sections_keep_anchors_without_body_h1(self):
        document = self.document()
        document['publication'] = {'title_in_template': True, 'heading_style': 'sections'}
        document['output_anchor_ids'] = ['title']
        for markup in (html.render_document(document, body_only=True, template_title=True), gutenberg.render_document(document)):
            self.assertNotIn('<h1', markup)
            self.assertNotIn('>Guide<', markup)
            self.assertNotIn('<h3', markup)
            self.assertIn('id="title"', markup)
            self.assertEqual(len(re.findall(r'<h2(?:\s|>)', markup)), 3)
        self.assertEqual(html.render_document(document).count('<h1'), 1)

    def test_missing_title_uses_metadata_with_unique_id(self):
        document = {'metadata': {'title': 'Guide'}, 'blocks': [
            {'id': 'publication-title', 'type': 'paragraph', 'content': 'Text'},
            {'id': 'section', 'type': 'heading', 'level': 4, 'content': 'Section'}]}
        projected = publication_document(document)
        self.assertEqual(projected['blocks'][0]['id'], 'publication-title-1')
        self.assertEqual(projected['blocks'][0]['content'], 'Guide')
        self.assertEqual(projected['blocks'][2]['level'], 2)


class FeedbackWorkflowTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp

    def linked_visual(self):
        document = ensure_review_document(self.root)
        visual = document['review']['complex_visuals'][0]
        visual.update({'source_block_id': 'photo', 'status': 'reclassified'})
        visual['accessibility']['short_alt'] = 'Accepted ALT'
        document['blocks'][2]['complex_visual_id'] = visual['id']
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        return document, visual

    def test_unchanged_visual_save_preserves_image_approval_and_optional_fields(self):
        _, visual = self.linked_visual()
        update_complex_visual(self.root, visual['id'], {'status': 'reclassified', **visual['accessibility'], 'adjacent_text': '', 'recovered_text': ''})
        current = ensure_review_document(self.root)
        self.assertEqual(current['blocks'][2]['review']['status'], 'approved')
        readiness = visual_readiness(current, current['review']['complex_visuals'][0])
        self.assertTrue(readiness['text_complete'])
        self.assertFalse(readiness['complete'])
        self.assertTrue(any(i['category'] == 'complex_visuals' for i in assess_document(current)['items']))

    def test_explicit_visual_review_approves_and_undo_restores_pending(self):
        _, visual = self.linked_visual()
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        update_complex_visual(self.root, visual['id'], {'status': 'reviewed', 'short_alt': 'Reviewed alternative'})
        current = ensure_review_document(self.root)
        self.assertEqual(current['blocks'][2]['review']['status'], 'approved')
        self.assertEqual(current['review']['complex_visuals'][0]['status'], 'reviewed')
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'][2]['review']['status'], 'needs_review')

    def test_adjacent_equivalent_is_published_when_long_description_is_empty(self):
        _, visual = self.linked_visual()
        update_complex_visual(self.root, visual['id'], {'status': 'reviewed', 'long_description': '', 'adjacent_text': 'Adjacent equivalent: the result is ten.'})
        current = ensure_review_document(self.root)
        self.assertTrue(visual_readiness(current, current['review']['complex_visuals'][0])['complete'])
        for markup in (html.render_document(current), gutenberg.render_document(current)):
            self.assertIn('Adjacent equivalent: the result is ten.', markup)

    def test_missing_equivalent_cannot_be_reviewed_and_not_applicable_is_reversible(self):
        _, visual = self.linked_visual()
        before = copy.deepcopy(ensure_review_document(self.root))
        with self.assertRaisesRegex(ValueError, 'either a long description'):
            update_complex_visual(self.root, visual['id'], {'status': 'reviewed', 'long_description': '', 'adjacent_text': ''})
        self.assertEqual(ensure_review_document(self.root), before)
        update_complex_visual(self.root, visual['id'], {'status': 'not_applicable', 'review_note': 'Simple screenshot; alt covers its purpose', 'long_description': ''})
        current = ensure_review_document(self.root)
        self.assertTrue(visual_readiness(current, current['review']['complex_visuals'][0])['complete'])
        self.assertFalse(current['blocks'][2].get('excluded', False))
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['review']['complex_visuals'], before['review']['complex_visuals'])

    def test_pending_visual_prevents_green_completion_and_export_links_pending_blocks(self):
        document, visual = self.linked_visual()
        for block in document['blocks']:
            block['alt'] = block.get('alt') or 'Alternative'
            block.setdefault('review', {})['status'] = 'approved'
        visual['accessibility']['long_description'] = ''
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        page = self.client.get('/structure').text
        self.assertNotIn('id="structure-review-complete"', page)
        self.assertIn('1 description review', page)
        self.assertIn('Recovered source text (optional)', page)
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        self.assertIn('href="/structure#block-photo">Source page 1 · Block 3: image', self.client.get('/export').text)

    def test_old_block_review_diagnostic_is_resolved_without_erasing_decision(self):
        document = ensure_review_document(self.root)
        document['review']['issues'] = [{'code': 'block_review_required', 'message': '1 block(s) require review before export.', 'block_ids': ['photo']}]
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        report = assess_document(document)
        note = next(i for i in report['items'] if i['category'] == 'diagnostics')
        self.assertEqual(note['status'], 'resolved')
        self.assertTrue(note['resolved_by_review'])
        self.assertIn('1 block(s)', note['original_message'])
        self.assertIn('Resolved extraction note', self.client.get('/accessibility').text)
        self.assertEqual(ensure_review_document(self.root)['review']['issues'], document['review']['issues'])
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        self.assertEqual(next(i for i in assess_document(ensure_review_document(self.root))['items'] if i['category'] == 'diagnostics')['status'], 'unresolved')

    def test_document_identity_and_single_disclaimer_on_every_screen(self):
        project = load_project(self.root)
        project['source']['original_filename'] = 'CITI & Training.pdf'
        save_project(self.root, project)
        for route in ('/', '/document', '/structure', '/accessibility', '/output-pages', '/preview', '/export'):
            page = self.client.get(route)
            self.assertEqual(page.status_code, 200, route)
            self.assertIn('Working on: <strong>CITI &amp; Training.pdf', page.text, route)
            self.assertRegex(page.text, r'<title>[^<]*CITI &amp; Training.pdf[^<]*</title>')
            self.assertEqual(page.text.count('do not certify WCAG'), 1)

    def test_semantic_and_axe_previews_load_same_local_images(self):
        before = ensure_review_document(self.root)
        for route in ('/api/preview/html', '/api/accessibility/preview'):
            response = self.client.get(route)
            self.assertIn('src="/api/preview/images/photo.png"', response.text)
            self.assertNotIn('src="images/photo.png"', response.text)
        self.assertEqual(self.client.get('/api/preview/images/photo.png').content, b'fixture image bytes')
        self.assertEqual(ensure_review_document(self.root), before)

    def test_template_export_settings_persist_undo_and_semantic_equivalence(self):
        approve_publication_fixture(self.root)
        before = ensure_review_document(self.root)
        response = self.client.post('/api/export', headers=self.headers, json={'target': 'html', 'title_in_template': True, 'heading_style': 'sections'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(ensure_review_document(self.root)['publication'], {'title_in_template': True, 'heading_style': 'sections'})
        body = next(d for d in response.json()['downloads'] if d['kind'] == 'template_body')
        self.assertNotIn('<h1', self.client.get(body['url']).text)
        standalone = next(d for d in response.json()['downloads'] if d['path'].endswith('.html') and d['kind'] == 'file')
        self.assertEqual(self.client.get(standalone['url']).text.count('<h1'), 1)
        for target in ('gutenberg', 'wordpress-xml'):
            result = self.client.post('/api/export', headers=self.headers, json={'target': target})
            self.assertEqual(result.status_code, 200, result.text)
        report_path, _ = validate_project_exports(self.root)
        report = json.loads(report_path.read_text())
        self.assertEqual(report['result'], 'PASS', report)
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])
        self.assertNotIn('publication', ensure_review_document(self.root))

    def test_url_label_edit_preserves_destination_rich_text_and_undo(self):
        document = ensure_review_document(self.root)
        paragraph = document['blocks'][1]
        paragraph['runs'] = [{'type': 'strong', 'text': 'Training: '}, {'type': 'link', 'text': 'https://example.test/training', 'url': 'https://example.test/training'}]
        paragraph['content'] = ''.join(r['text'] for r in paragraph['runs'])
        paragraph['review'] = {'status': 'approved'}
        stamp_fixture_approvals(document)
        save_review_document(self.root, document)
        self.assertIn('URL used as link text', self.client.get('/accessibility').text)
        self.assertIn('link-text-form', self.client.get('/structure').text)
        update_block(self.root, 'p', {'content': paragraph['content'], 'review_status': 'approved'})
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['runs'], paragraph['runs'])
        response = self.client.post('/api/blocks/p', headers=self.headers, json={'link_index': 1, 'link_text': 'CITI training registration'})
        self.assertEqual(response.status_code, 200, response.text)
        current = ensure_review_document(self.root)
        self.assertEqual(current['blocks'][1]['runs'][1]['url'], 'https://example.test/training')
        self.assertEqual(current['blocks'][1]['review']['status'], 'needs_review')
        self.assertIn('<strong>Training: </strong><a href="https://example.test/training">CITI training registration</a>', html.render_document(current))
        self.assertFalse(any(i['title'] == 'URL used as link text' for i in assess_document(current)['items']))
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'][1]['runs'], paragraph['runs'])
